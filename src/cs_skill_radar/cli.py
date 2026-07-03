"""Command-line interface for CS Skill Radar."""

from __future__ import annotations

import argparse
from pathlib import Path

from cs_skill_radar.analytics.exports import export_stats_csv, export_stats_json
from cs_skill_radar.analytics.skill_stats import compute_skill_stats
from cs_skill_radar.config import DEFAULT_DATABASE_PATH, DEFAULT_EXPORTS_DIR
from cs_skill_radar.db import SkillRadarDatabase
from cs_skill_radar.extraction.skill_extractor import extract_skills
from cs_skill_radar.sources.manual import load_manual_jobs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cs-skill-radar")
    parser.add_argument("--db", default=str(DEFAULT_DATABASE_PATH), help="SQLite database path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_manual = subparsers.add_parser("import-manual")
    import_manual.add_argument("--file", required=True, help="Manual JSON input path")

    subparsers.add_parser("extract-skills")
    subparsers.add_parser("compute-stats")

    export_stats = subparsers.add_parser("export-stats")
    export_stats.add_argument("--format", choices=("json", "csv"), required=True)
    export_stats.add_argument("--output", help="Output file path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    db = SkillRadarDatabase(args.db)
    db.initialize()

    if args.command == "import-manual":
        jobs = load_manual_jobs(args.file)
        db.save_jobs(jobs)
        print(f"Imported {len(jobs)} manual jobs.")
        return 0

    if args.command == "extract-skills":
        jobs = db.list_jobs()
        extracted = []
        for job in jobs:
            extracted.extend(extract_skills(job.description, job_id=job.id))
        db.save_extracted_skills(extracted)
        print(f"Extracted {len(extracted)} skills.")
        return 0

    if args.command == "compute-stats":
        stats = compute_skill_stats(db.list_jobs(), db.list_extracted_skills())
        print(f"Computed {len(stats)} skill stats.")
        return 0

    if args.command == "export-stats":
        stats = compute_skill_stats(db.list_jobs(), db.list_extracted_skills())
        output = _default_export_path(args.format, args.output)
        if args.format == "json":
            export_stats_json(stats, output)
        else:
            export_stats_csv(stats, output)
        print(f"Exported {len(stats)} stats to {output}.")
        return 0

    raise ValueError(f"unknown command: {args.command}")


def _default_export_path(format_name: str, output: str | None) -> Path:
    if output:
        return Path(output)
    return DEFAULT_EXPORTS_DIR / f"skill_stats.{format_name}"


if __name__ == "__main__":
    raise SystemExit(main())
