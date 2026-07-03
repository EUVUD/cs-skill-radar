"""Lever public postings API adapter."""

from __future__ import annotations

from collections.abc import Iterable

from cs_skill_radar.models import JobPosting
from cs_skill_radar.sources.base import SourceAdapter


class LeverAdapter(SourceAdapter):
    source_name = "lever"

    def __init__(self, company_slug: str) -> None:
        self.company_slug = company_slug

    @property
    def api_url(self) -> str:
        return f"https://api.lever.co/v0/postings/{self.company_slug}?mode=json"

    def collect(self) -> Iterable[JobPosting]:
        raise NotImplementedError("Lever public API collection is a follow-up adapter.")
