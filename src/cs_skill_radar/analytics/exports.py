"""JSON and CSV exports for skill statistics."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from cs_skill_radar.models import SkillStat


def export_stats_json(stats: list[SkillStat], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [stat.model_dump(mode="json") for stat in stats]
    output_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return output_path


def export_stats_csv(stats: list[SkillStat], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "normalized_role",
        "skill",
        "job_count",
        "required_count",
        "preferred_count",
        "nice_to_have_count",
        "mentioned_count",
        "percentage",
        "time_window",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for stat in stats:
            writer.writerow(stat.model_dump(mode="json"))
    return output_path
