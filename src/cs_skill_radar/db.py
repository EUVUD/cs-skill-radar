"""SQLite persistence boundary for CS Skill Radar."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable

from cs_skill_radar.models import ExtractedSkill, JobPosting, utc_now


class SkillRadarDatabase:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    company TEXT NOT NULL,
                    title TEXT NOT NULL,
                    normalized_role TEXT NOT NULL,
                    location TEXT,
                    seniority TEXT,
                    description TEXT NOT NULL,
                    description_hash TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_source_url
                    ON jobs(source_url);

                CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_description_hash
                    ON jobs(description_hash);

                CREATE TABLE IF NOT EXISTS extracted_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL REFERENCES jobs(id),
                    raw_skill TEXT NOT NULL,
                    normalized_skill TEXT NOT NULL,
                    requirement_type TEXT NOT NULL,
                    confidence REAL NOT NULL
                );
                """
            )

    def find_duplicate_job_id(self, job: JobPosting) -> int | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT id FROM jobs
                WHERE source_url = ? OR description_hash = ?
                ORDER BY id
                LIMIT 1
                """,
                (job.source_url, job.description_hash),
            ).fetchone()
        return int(row["id"]) if row else None

    def save_job(self, job: JobPosting) -> int:
        self.initialize()
        duplicate_id = self.find_duplicate_job_id(job)
        if duplicate_id is not None:
            return duplicate_id

        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO jobs (
                    source,
                    source_url,
                    company,
                    title,
                    normalized_role,
                    location,
                    seniority,
                    description,
                    description_hash,
                    first_seen_at,
                    last_seen_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.source,
                    job.source_url,
                    job.company,
                    job.title,
                    job.normalized_role,
                    job.location,
                    job.seniority,
                    job.description,
                    job.description_hash,
                    job.first_seen_at.isoformat(),
                    job.last_seen_at.isoformat(),
                ),
            )
            return int(cursor.lastrowid)

    def save_jobs(self, jobs: Iterable[JobPosting]) -> list[int]:
        return [self.save_job(job) for job in jobs]

    def save_or_update_seen_job(self, job: JobPosting, seen_at: datetime | None = None) -> int:
        self.initialize()
        seen_time = seen_at or utc_now()
        duplicate_id = self.find_duplicate_job_id(job)
        if duplicate_id is not None:
            with self.connect() as connection:
                connection.execute(
                    """
                    UPDATE jobs
                    SET last_seen_at = ?
                    WHERE id = ?
                    """,
                    (seen_time.isoformat(), duplicate_id),
                )
            return duplicate_id

        seen_job = job.model_copy(
            update={
                "first_seen_at": seen_time,
                "last_seen_at": seen_time,
            }
        )
        return self.save_job(seen_job)

    def save_or_update_seen_jobs(
        self,
        jobs: Iterable[JobPosting],
        seen_at: datetime | None = None,
    ) -> list[int]:
        seen_time = seen_at or utc_now()
        return [self.save_or_update_seen_job(job, seen_at=seen_time) for job in jobs]

    def list_jobs(self) -> list[JobPosting]:
        self.initialize()
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM jobs ORDER BY id").fetchall()
        return [self._job_from_row(row) for row in rows]

    def save_extracted_skill(self, skill: ExtractedSkill) -> int:
        self.initialize()
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO extracted_skills (
                    job_id,
                    raw_skill,
                    normalized_skill,
                    requirement_type,
                    confidence
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    skill.job_id,
                    skill.raw_skill,
                    skill.normalized_skill,
                    skill.requirement_type,
                    skill.confidence,
                ),
            )
            return int(cursor.lastrowid)

    def save_extracted_skills(self, skills: Iterable[ExtractedSkill]) -> list[int]:
        return [self.save_extracted_skill(skill) for skill in skills]

    def list_extracted_skills(self) -> list[ExtractedSkill]:
        self.initialize()
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM extracted_skills ORDER BY id").fetchall()
        return [
            ExtractedSkill(
                id=int(row["id"]),
                job_id=int(row["job_id"]),
                raw_skill=row["raw_skill"],
                normalized_skill=row["normalized_skill"],
                requirement_type=row["requirement_type"],
                confidence=float(row["confidence"]),
            )
            for row in rows
        ]

    def _job_from_row(self, row: sqlite3.Row) -> JobPosting:
        return JobPosting(
            id=int(row["id"]),
            source=row["source"],
            source_url=row["source_url"],
            company=row["company"],
            title=row["title"],
            normalized_role=row["normalized_role"],
            location=row["location"],
            seniority=row["seniority"],
            description=row["description"],
            description_hash=row["description_hash"],
            first_seen_at=row["first_seen_at"],
            last_seen_at=row["last_seen_at"],
        )
