import json

from cs_skill_radar.cli import main
from cs_skill_radar.db import SkillRadarDatabase


def write_company_config(path, companies=None):
    payload = {
        "companies": companies
        or [
            {
                "name": "ExampleCloud",
                "board_token": "examplecloud",
                "enabled": True,
            }
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


def load_greenhouse_fixture():
    fixture_path = __file__.replace("test_greenhouse_cli.py", "fixtures/greenhouse_jobs.json")
    with open(fixture_path, encoding="utf-8") as fixture:
        return json.load(fixture)


def test_cli_import_greenhouse_saves_matching_jobs_and_reports_summary(tmp_path, capsys):
    db_path = tmp_path / "jobs.sqlite"
    config_path = write_company_config(tmp_path / "companies.json")

    result = main(
        [
            "--db",
            str(db_path),
            "import-greenhouse",
            "--companies",
            str(config_path),
        ],
        greenhouse_fetcher=lambda url, timeout_seconds, user_agent: load_greenhouse_fixture(),
    )

    captured = capsys.readouterr()
    jobs = SkillRadarDatabase(db_path).list_jobs()
    assert result == 0
    assert len(jobs) == 2
    assert {job.normalized_role for job in jobs} == {"backend_engineer", "platform_engineer"}
    assert "Imported 2 Greenhouse jobs from 1 companies" in captured.out
    assert "skipped 4 jobs" in captured.out


def test_cli_import_greenhouse_reports_company_failures_and_continues(tmp_path, capsys):
    db_path = tmp_path / "jobs.sqlite"
    config_path = write_company_config(
        tmp_path / "companies.json",
        companies=[
            {"name": "BrokenCo", "board_token": "broken", "enabled": True},
            {"name": "ExampleCloud", "board_token": "examplecloud", "enabled": True},
        ],
    )

    def fake_fetch(url, timeout_seconds, user_agent):
        if "broken" in url:
            raise RuntimeError("temporary outage")
        return load_greenhouse_fixture()

    result = main(
        [
            "--db",
            str(db_path),
            "import-greenhouse",
            "--companies",
            str(config_path),
        ],
        greenhouse_fetcher=fake_fetch,
    )

    captured = capsys.readouterr()
    assert result == 0
    assert len(SkillRadarDatabase(db_path).list_jobs()) == 2
    assert "failed 1 companies" in captured.out
    assert "BrokenCo: temporary outage" in captured.out


def test_cli_import_greenhouse_rejects_bad_config_before_fetch(tmp_path, capsys):
    db_path = tmp_path / "jobs.sqlite"
    config_path = write_company_config(
        tmp_path / "companies.json",
        companies=[{"name": "MissingToken", "enabled": True}],
    )
    fetch_called = False

    def fake_fetch(url, timeout_seconds, user_agent):
        nonlocal fetch_called
        fetch_called = True
        return load_greenhouse_fixture()

    result = main(
        [
            "--db",
            str(db_path),
            "import-greenhouse",
            "--companies",
            str(config_path),
        ],
        greenhouse_fetcher=fake_fetch,
    )

    captured = capsys.readouterr()
    assert result == 2
    assert fetch_called is False
    assert "invalid Greenhouse company config" in captured.err
