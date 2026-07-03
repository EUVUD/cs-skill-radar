"""Greenhouse public job board API adapter."""

from __future__ import annotations

from collections.abc import Iterable

from cs_skill_radar.models import JobPosting
from cs_skill_radar.sources.base import SourceAdapter


class GreenhouseAdapter(SourceAdapter):
    source_name = "greenhouse"

    def __init__(self, company_slug: str) -> None:
        self.company_slug = company_slug

    @property
    def api_url(self) -> str:
        return f"https://boards-api.greenhouse.io/v1/boards/{self.company_slug}/jobs"

    def collect(self) -> Iterable[JobPosting]:
        raise NotImplementedError("Greenhouse public API collection is a follow-up adapter.")
