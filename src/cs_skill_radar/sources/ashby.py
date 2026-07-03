"""Ashby public postings API adapter."""

from __future__ import annotations

from collections.abc import Iterable

from cs_skill_radar.models import JobPosting
from cs_skill_radar.sources.base import SourceAdapter


class AshbyAdapter(SourceAdapter):
    source_name = "ashby"

    def __init__(self, company_slug: str) -> None:
        self.company_slug = company_slug

    @property
    def api_url(self) -> str:
        return f"https://api.ashbyhq.com/posting-api/job-board/{self.company_slug}"

    def collect(self) -> Iterable[JobPosting]:
        raise NotImplementedError("Ashby public API collection is a follow-up adapter.")
