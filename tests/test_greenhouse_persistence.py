from datetime import datetime, timezone

from cs_skill_radar.db import SkillRadarDatabase
from cs_skill_radar.models import JobPosting


def make_greenhouse_job() -> JobPosting:
    return JobPosting(
        source="greenhouse",
        source_url="https://boards.greenhouse.io/examplecloud/jobs/101",
        company="ExampleCloud",
        title="Backend Engineer",
        normalized_role="backend_engineer",
        location="Remote",
        description="Build Python services with PostgreSQL.",
    )


def test_save_or_update_seen_job_sets_local_first_and_last_seen(tmp_path):
    db = SkillRadarDatabase(tmp_path / "jobs.sqlite")
    seen_at = datetime(2026, 7, 3, 9, 0, tzinfo=timezone.utc)

    job_id = db.save_or_update_seen_job(make_greenhouse_job(), seen_at=seen_at)

    saved = db.list_jobs()[0]
    assert job_id == saved.id
    assert saved.first_seen_at == seen_at
    assert saved.last_seen_at == seen_at


def test_save_or_update_seen_job_updates_existing_last_seen_without_duplicate(tmp_path):
    db = SkillRadarDatabase(tmp_path / "jobs.sqlite")
    first_seen = datetime(2026, 7, 3, 9, 0, tzinfo=timezone.utc)
    second_seen = datetime(2026, 7, 4, 9, 0, tzinfo=timezone.utc)

    first_id = db.save_or_update_seen_job(make_greenhouse_job(), seen_at=first_seen)
    second_id = db.save_or_update_seen_job(
        make_greenhouse_job().model_copy(update={"title": "Backend Engineer II"}),
        seen_at=second_seen,
    )

    jobs = db.list_jobs()
    assert second_id == first_id
    assert len(jobs) == 1
    assert jobs[0].title == "Backend Engineer"
    assert jobs[0].first_seen_at == first_seen
    assert jobs[0].last_seen_at == second_seen
