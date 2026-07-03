"""Manual JSON source adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cs_skill_radar.models import JobPosting
from cs_skill_radar.sources.base import SourceAdapter


def load_manual_jobs(path: str | Path) -> list[JobPosting]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    records = data["jobs"] if isinstance(data, dict) and "jobs" in data else data
    if not isinstance(records, list):
        raise ValueError("manual job input must be a list or an object with a jobs list")
    return [_job_from_record(record) for record in records]


def _job_from_record(record: dict[str, Any]) -> JobPosting:
    values = dict(record)
    values["source"] = values.get("source", "manual")
    if "source_url" not in values:
        company = str(values.get("company", "unknown")).strip().lower().replace(" ", "-")
        title = str(values.get("title", "job")).strip().lower().replace(" ", "-")
        values["source_url"] = f"manual://{company}/{title}"
    return JobPosting(**values)


class ManualAdapter(SourceAdapter):
    source_name = "manual"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def collect(self) -> list[JobPosting]:
        return load_manual_jobs(self.path)
