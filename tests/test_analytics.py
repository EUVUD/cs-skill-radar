from cs_skill_radar.analytics.skill_stats import compute_skill_stats
from cs_skill_radar.models import ExtractedSkill, JobPosting


def make_job(job_id: int, role: str = "backend_engineer") -> JobPosting:
    return JobPosting(
        id=job_id,
        source="manual",
        source_url=f"manual://job-{job_id}",
        company="Acme",
        title="Backend Engineer",
        normalized_role=role,
        location="Remote",
        seniority="mid",
        description="Python Python Python and Docker.",
    )


def test_repeated_skill_mentions_count_once_per_job():
    jobs = [make_job(1), make_job(2)]
    skills = [
        ExtractedSkill(
            job_id=1,
            raw_skill="Python",
            normalized_skill="Python",
            requirement_type="required",
            confidence=0.95,
        ),
        ExtractedSkill(
            job_id=1,
            raw_skill="Python",
            normalized_skill="Python",
            requirement_type="mentioned",
            confidence=0.80,
        ),
        ExtractedSkill(
            job_id=2,
            raw_skill="Docker",
            normalized_skill="Docker",
            requirement_type="preferred",
            confidence=0.90,
        ),
    ]

    stats = compute_skill_stats(jobs, skills)
    python = next(stat for stat in stats if stat.skill == "Python")

    assert python.normalized_role == "backend_engineer"
    assert python.job_count == 2
    assert python.required_count == 1
    assert python.mentioned_count == 0
    assert python.percentage == 50.0
