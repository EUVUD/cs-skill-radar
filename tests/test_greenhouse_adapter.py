import json
from types import SimpleNamespace

import pytest

from cs_skill_radar.sources import greenhouse as greenhouse_module
from cs_skill_radar.models import JobPosting
from cs_skill_radar.sources.greenhouse import (
    GreenhouseAdapter,
    collect_greenhouse_jobs,
    fetch_greenhouse_json,
    load_greenhouse_config,
)


def write_company_config(path, companies=None):
    payload = {
        "companies": companies
        or [
            {
                "name": "ExampleCloud",
                "board_token": "examplecloud",
                "enabled": True,
                "homepage": "https://boards.greenhouse.io/examplecloud",
            },
            {
                "name": "DisabledCo",
                "board_token": "disabledco",
                "enabled": False,
            },
        ],
        "target_roles": [
            {
                "normalized_role": "backend_engineer",
                "title_keywords": ["backend engineer"],
                "department_keywords": ["engineering"],
            },
            {
                "normalized_role": "platform_engineer",
                "title_keywords": ["platform engineer"],
                "department_keywords": ["infrastructure"],
            },
        ],
        "exclude_title_keywords": ["sales", "recruiter", "marketing"],
        "languages": ["en"],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def load_fixture(name):
    fixture_path = __file__.replace("test_greenhouse_adapter.py", f"fixtures/{name}")
    with open(fixture_path, encoding="utf-8") as fixture:
        return json.load(fixture)


def test_load_greenhouse_config_uses_enabled_companies_and_filters(tmp_path):
    path = write_company_config(tmp_path / "companies.json")

    config = load_greenhouse_config(path)

    assert [company.name for company in config.enabled_companies] == ["ExampleCloud"]
    assert config.enabled_companies[0].board_token == "examplecloud"
    assert config.target_roles[0].normalized_role == "backend_engineer"
    assert config.exclude_title_keywords == ("sales", "recruiter", "marketing")
    assert config.languages == ("en",)


def test_load_greenhouse_config_rejects_malformed_entries(tmp_path):
    path = write_company_config(
        tmp_path / "companies.json",
        companies=[{"name": "MissingToken", "enabled": True}],
    )

    with pytest.raises(ValueError, match="board_token"):
        load_greenhouse_config(path)


def test_greenhouse_adapter_filters_and_maps_jobs(tmp_path):
    config = load_greenhouse_config(write_company_config(tmp_path / "companies.json"))
    payload = load_fixture("greenhouse_jobs.json")
    calls = []

    def fake_fetch(url, timeout_seconds, user_agent):
        calls.append((url, timeout_seconds, user_agent))
        return payload

    adapter = GreenhouseAdapter(
        company_slug="examplecloud",
        company_name="ExampleCloud",
        target_roles=config.target_roles,
        exclude_title_keywords=config.exclude_title_keywords,
        languages=config.languages,
        fetcher=fake_fetch,
    )

    jobs = adapter.collect()

    assert [job.title for job in jobs] == ["Backend Engineer", "Platform Engineer"]
    assert all(isinstance(job, JobPosting) for job in jobs)
    assert jobs[0].source == "greenhouse"
    assert jobs[0].company == "ExampleCloud"
    assert jobs[0].source_url == "https://boards.greenhouse.io/examplecloud/jobs/101"
    assert jobs[0].location == "Remote"
    assert jobs[0].normalized_role == "backend_engineer"
    assert "Build Python services with PostgreSQL." in jobs[0].description
    assert jobs[1].source_url == "https://boards.greenhouse.io/examplecloud/jobs/102"
    assert jobs[1].normalized_role == "platform_engineer"
    assert adapter.skipped_count == 4
    assert calls == [
        (
            "https://boards-api.greenhouse.io/v1/boards/examplecloud/jobs?content=true",
            15.0,
            "cs-skill-radar/0.1 (+https://github.com/EUVUD/cs-skill-radar)",
        )
    ]


def test_greenhouse_collection_continues_after_company_failure(tmp_path):
    config = load_greenhouse_config(
        write_company_config(
            tmp_path / "companies.json",
            companies=[
                {"name": "BrokenCo", "board_token": "broken", "enabled": True},
                {"name": "ExampleCloud", "board_token": "examplecloud", "enabled": True},
            ],
        )
    )
    payload = load_fixture("greenhouse_jobs.json")

    def fake_fetch(url, timeout_seconds, user_agent):
        if "broken" in url:
            raise RuntimeError("temporary outage")
        return payload

    result = collect_greenhouse_jobs(config, fetcher=fake_fetch)

    assert [failure.company for failure in result.failed_companies] == ["BrokenCo"]
    assert result.successful_companies == ("ExampleCloud",)
    assert len(result.jobs) == 2


def test_greenhouse_adapter_uses_only_public_board_jobs_endpoint(tmp_path):
    config = load_greenhouse_config(write_company_config(tmp_path / "companies.json"))
    payload = load_fixture("greenhouse_jobs.json")
    requested_urls = []

    def fake_fetch(url, timeout_seconds, user_agent):
        requested_urls.append(url)
        return payload

    GreenhouseAdapter(
        company_slug="examplecloud",
        company_name="ExampleCloud",
        target_roles=config.target_roles,
        exclude_title_keywords=config.exclude_title_keywords,
        languages=config.languages,
        fetcher=fake_fetch,
    ).collect()

    assert requested_urls == [
        "https://boards-api.greenhouse.io/v1/boards/examplecloud/jobs?content=true"
    ]
    forbidden_fragments = (
        "linkedin",
        "indeed",
        "glassdoor",
        "applications",
        "captcha",
        "cloudflare",
        "proxy",
    )
    assert not any(fragment in requested_urls[0].lower() for fragment in forbidden_fragments)


def test_fetch_greenhouse_json_uses_system_ca_when_default_python_ca_is_missing(
    tmp_path,
    monkeypatch,
):
    fallback_ca = tmp_path / "cert.pem"
    fallback_ca.write_text("certificate bundle", encoding="utf-8")
    captured = {}

    class FakeHeaders:
        def get_content_charset(self):
            return "utf-8"

    class FakeResponse:
        headers = FakeHeaders()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return b'{"jobs": []}'

    def fake_create_default_context(cafile=None):
        return ("ssl-context", cafile)

    def fake_urlopen(request, timeout, context):
        captured["timeout"] = timeout
        captured["context"] = context
        return FakeResponse()

    monkeypatch.setattr(
        greenhouse_module.ssl,
        "get_default_verify_paths",
        lambda: SimpleNamespace(cafile="/missing/python/cert.pem"),
    )
    monkeypatch.setattr(greenhouse_module.ssl, "create_default_context", fake_create_default_context)
    monkeypatch.setattr(greenhouse_module, "urlopen", fake_urlopen)
    monkeypatch.setattr(greenhouse_module, "CA_BUNDLE_CANDIDATES", (fallback_ca,))

    payload = fetch_greenhouse_json("https://boards-api.greenhouse.io/v1/boards/example/jobs")

    assert payload == {"jobs": []}
    assert captured["timeout"] == 15.0
    assert captured["context"] == ("ssl-context", str(fallback_ca))
