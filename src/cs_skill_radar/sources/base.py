"""Base interfaces for source adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from cs_skill_radar.models import JobPosting


class SourceAdapter(ABC):
    source_name: str

    @abstractmethod
    def collect(self) -> Iterable[JobPosting]:
        """Collect source data and return normalized job postings."""
