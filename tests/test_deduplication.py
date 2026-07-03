from cs_skill_radar.db import SkillRadarDatabase
from cs_skill_radar.models import JobPosting


def make_job(source_url: str, description: str) -> JobPosting:
    return JobPosting(
        source="manual",
        source_url=source_url,
        company="Acme",
        title="Backend Engineer",
        normalized_role="backend_engineer",
        location="Remote",
        seniority="mid",
        description=description,
    )


def test_database_deduplicates_jobs_by_source_url(tmp_path):
    db = SkillRadarDatabase(tmp_path / "jobs.sqlite")
    db.initialize()
    job = make_job("manual://acme/backend", "Python and PostgreSQL required.")

    first_id = db.save_job(job)
    second_id = db.save_job(job.model_copy(update={"title": "Backend Engineer II"}))

    assert second_id == first_id
    assert len(db.list_jobs()) == 1


def test_database_deduplicates_jobs_by_description_hash(tmp_path):
    db = SkillRadarDatabase(tmp_path / "jobs.sqlite")
    db.initialize()
    first = make_job("manual://acme/backend-1", "Python and PostgreSQL required.")
    duplicate = make_job("manual://acme/backend-2", " Python and PostgreSQL required. ")

    first_id = db.save_job(first)
    duplicate_id = db.save_job(duplicate)

    assert duplicate_id == first_id
    assert len(db.list_jobs()) == 1
