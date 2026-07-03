"""Greenhouse public job board API adapter."""

from __future__ import annotations

import html
import json
import re
import ssl
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from cs_skill_radar.compliance.denylist import assert_allowed_default_source
from cs_skill_radar.models import JobPosting
from cs_skill_radar.sources.base import SourceAdapter

DEFAULT_TIMEOUT_SECONDS = 15.0
DEFAULT_USER_AGENT = "cs-skill-radar/0.1 (+https://github.com/EUVUD/cs-skill-radar)"
CA_BUNDLE_CANDIDATES = (
    Path("/etc/ssl/cert.pem"),
    Path("/opt/homebrew/etc/openssl@3/cert.pem"),
    Path("/usr/local/etc/openssl@3/cert.pem"),
)

FetchJson = Callable[[str, float, str], dict[str, Any]]


class GreenhouseCompany(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    board_token: str
    enabled: bool = True
    homepage: str | None = None

    @field_validator("name", "board_token")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be blank")
        return cleaned


class TargetRoleFilter(BaseModel):
    model_config = ConfigDict(extra="ignore")

    normalized_role: str
    title_keywords: tuple[str, ...] = Field(default_factory=tuple)
    department_keywords: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("normalized_role")
    @classmethod
    def strip_normalized_role(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("normalized_role must not be blank")
        return cleaned

    @field_validator("title_keywords", "department_keywords", mode="before")
    @classmethod
    def clean_keyword_tuple(cls, value: Any) -> tuple[str, ...]:
        if value is None:
            return ()
        if not isinstance(value, list | tuple):
            raise ValueError("keywords must be a list")
        return tuple(_clean_keyword(keyword) for keyword in value if _clean_keyword(keyword))


class GreenhouseImportConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    companies: tuple[GreenhouseCompany, ...]
    target_roles: tuple[TargetRoleFilter, ...] = Field(default_factory=tuple)
    exclude_title_keywords: tuple[str, ...] = Field(default_factory=tuple)
    languages: tuple[str, ...] = Field(default_factory=lambda: ("en",))

    @field_validator("companies")
    @classmethod
    def require_companies(cls, value: tuple[GreenhouseCompany, ...]) -> tuple[GreenhouseCompany, ...]:
        if not value:
            raise ValueError("companies must not be empty")
        return value

    @field_validator("exclude_title_keywords", "languages", mode="before")
    @classmethod
    def clean_string_tuple(cls, value: Any) -> tuple[str, ...]:
        if value is None:
            return ()
        if not isinstance(value, list | tuple):
            raise ValueError("value must be a list")
        return tuple(_clean_keyword(item) for item in value if _clean_keyword(item))

    @property
    def enabled_companies(self) -> tuple[GreenhouseCompany, ...]:
        return tuple(company for company in self.companies if company.enabled)


@dataclass(frozen=True)
class GreenhouseCompanyFailure:
    company: str
    board_token: str
    error: str


@dataclass(frozen=True)
class GreenhouseCollectionResult:
    jobs: list[JobPosting]
    successful_companies: tuple[str, ...]
    failed_companies: tuple[GreenhouseCompanyFailure, ...]
    skipped_jobs: int


def load_greenhouse_config(path: str | Path) -> GreenhouseImportConfig:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid Greenhouse company config JSON: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"could not read Greenhouse company config: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Greenhouse company config must be a JSON object")

    try:
        return GreenhouseImportConfig.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"invalid Greenhouse company config: {exc}") from exc


def fetch_greenhouse_json(
    url: str,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    user_agent: str = DEFAULT_USER_AGENT,
) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": user_agent,
        },
    )
    with urlopen(request, timeout=timeout_seconds, context=_ssl_context()) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        payload = json.loads(response.read().decode(charset))
    if not isinstance(payload, dict):
        raise ValueError("Greenhouse response must be a JSON object")
    return payload


def _ssl_context() -> ssl.SSLContext | None:
    default_cafile = ssl.get_default_verify_paths().cafile
    if default_cafile and Path(default_cafile).exists():
        return None
    for candidate in CA_BUNDLE_CANDIDATES:
        if candidate.exists():
            return ssl.create_default_context(cafile=str(candidate))
    return None


def collect_greenhouse_jobs(
    config: GreenhouseImportConfig,
    fetcher: FetchJson | None = None,
) -> GreenhouseCollectionResult:
    assert_allowed_default_source(GreenhouseAdapter.source_name)
    jobs: list[JobPosting] = []
    successful_companies: list[str] = []
    failed_companies: list[GreenhouseCompanyFailure] = []
    skipped_jobs = 0

    for company in config.enabled_companies:
        adapter = GreenhouseAdapter(
            company_slug=company.board_token,
            company_name=company.name,
            target_roles=config.target_roles,
            exclude_title_keywords=config.exclude_title_keywords,
            languages=config.languages,
            fetcher=fetcher,
        )
        try:
            company_jobs = adapter.collect()
        except Exception as exc:
            failed_companies.append(
                GreenhouseCompanyFailure(
                    company=company.name,
                    board_token=company.board_token,
                    error=str(exc),
                )
            )
            continue
        jobs.extend(company_jobs)
        skipped_jobs += adapter.skipped_count
        successful_companies.append(company.name)

    return GreenhouseCollectionResult(
        jobs=jobs,
        successful_companies=tuple(successful_companies),
        failed_companies=tuple(failed_companies),
        skipped_jobs=skipped_jobs,
    )


class GreenhouseAdapter(SourceAdapter):
    source_name = "greenhouse"

    def __init__(
        self,
        company_slug: str,
        company_name: str | None = None,
        target_roles: Iterable[TargetRoleFilter] = (),
        exclude_title_keywords: Iterable[str] = (),
        languages: Iterable[str] = ("en",),
        fetcher: FetchJson | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        assert_allowed_default_source(self.source_name)
        self.company_slug = company_slug.strip()
        if not self.company_slug:
            raise ValueError("company_slug must not be blank")
        self.company_name = (company_name or company_slug).strip()
        if not self.company_name:
            raise ValueError("company_name must not be blank")
        self.target_roles = tuple(target_roles)
        self.exclude_title_keywords = tuple(_clean_keyword(item) for item in exclude_title_keywords if _clean_keyword(item))
        self.languages = tuple(_clean_keyword(item) for item in languages if _clean_keyword(item))
        self.fetcher = fetcher or fetch_greenhouse_json
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent
        self.skipped_count = 0

    @property
    def api_url(self) -> str:
        return f"https://boards-api.greenhouse.io/v1/boards/{self.company_slug}/jobs?content=true"

    def collect(self) -> list[JobPosting]:
        payload = self.fetcher(self.api_url, self.timeout_seconds, self.user_agent)
        records = payload.get("jobs")
        if not isinstance(records, list):
            raise ValueError("Greenhouse response must contain a jobs list")

        self.skipped_count = 0
        jobs: list[JobPosting] = []
        for record in records:
            if not isinstance(record, dict):
                self.skipped_count += 1
                continue
            job = self._job_from_record(record)
            if job is None:
                self.skipped_count += 1
                continue
            jobs.append(job)
        return jobs

    def _job_from_record(self, record: dict[str, Any]) -> JobPosting | None:
        if "internal_job_id" in record and record.get("internal_job_id") is None:
            return None

        normalized_role = _match_normalized_role(
            record=record,
            target_roles=self.target_roles,
            exclude_title_keywords=self.exclude_title_keywords,
            languages=self.languages,
        )
        if normalized_role is None:
            return None

        description = _description_text(record.get("content"))
        if not description:
            return None

        title = str(record.get("title", "")).strip()
        if not title:
            return None

        source_url = _source_url(record, self.company_slug)
        if not source_url:
            return None

        return JobPosting(
            source=self.source_name,
            source_url=source_url,
            company=self.company_name,
            title=title,
            normalized_role=normalized_role,
            location=_location_name(record),
            description=description,
        )


def _match_normalized_role(
    record: dict[str, Any],
    target_roles: Iterable[TargetRoleFilter],
    exclude_title_keywords: Iterable[str],
    languages: Iterable[str],
) -> str | None:
    language = _clean_keyword(record.get("language"))
    accepted_languages = tuple(languages)
    if accepted_languages and language not in accepted_languages:
        return None

    title = _clean_keyword(record.get("title"))
    if any(keyword in title for keyword in exclude_title_keywords):
        return None

    departments = tuple(_clean_keyword(name) for name in _department_names(record))
    for role in target_roles:
        if any(keyword in title for keyword in role.title_keywords):
            return role.normalized_role
    for role in target_roles:
        if any(
            keyword in department
            for keyword in role.department_keywords
            for department in departments
        ):
            return role.normalized_role
    return None


def _description_text(value: Any) -> str:
    if value is None:
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split()).strip()


def _source_url(record: dict[str, Any], company_slug: str) -> str:
    absolute_url = str(record.get("absolute_url") or "").strip()
    if absolute_url:
        return absolute_url
    job_id = record.get("id")
    if job_id is None:
        return ""
    return f"https://boards.greenhouse.io/{company_slug}/jobs/{job_id}"


def _location_name(record: dict[str, Any]) -> str | None:
    location = record.get("location")
    if isinstance(location, dict):
        name = str(location.get("name") or "").strip()
        return name or None
    return None


def _department_names(record: dict[str, Any]) -> tuple[str, ...]:
    departments = record.get("departments")
    if not isinstance(departments, list):
        return ()
    names: list[str] = []
    for department in departments:
        if not isinstance(department, dict):
            continue
        name = str(department.get("name") or "").strip()
        if name:
            names.append(name)
    return tuple(names)


def _clean_keyword(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())
