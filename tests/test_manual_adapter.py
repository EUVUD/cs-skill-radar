from cs_skill_radar.models import JobPosting
from cs_skill_radar.sources.manual import load_manual_jobs


def test_manual_adapter_loads_json_jobs(tmp_path):
    path = tmp_path / "jobs.json"
    path.write_text(
        """
        [
          {
            "source_url": "manual://acme/backend",
            "company": "Acme",
            "title": "Backend Engineer",
            "normalized_role": "backend_engineer",
            "location": "Remote",
            "seniority": "mid",
            "description": "We need Python, PostgreSQL, and Kubernetes."
          }
        ]
        """,
        encoding="utf-8",
    )

    jobs = load_manual_jobs(path)

    assert len(jobs) == 1
    assert isinstance(jobs[0], JobPosting)
    assert jobs[0].source == "manual"
    assert jobs[0].description_hash
