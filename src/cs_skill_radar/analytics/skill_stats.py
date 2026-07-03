"""Role-level skill statistics."""

from __future__ import annotations

from collections import Counter, defaultdict

from cs_skill_radar.extraction.skill_extractor import REQUIREMENT_RANK
from cs_skill_radar.models import ExtractedSkill, JobPosting, RequirementType, SkillStat


def compute_skill_stats(jobs: list[JobPosting], skills: list[ExtractedSkill]) -> list[SkillStat]:
    jobs_by_id = {job.id: job for job in jobs if job.id is not None}
    role_job_counts = Counter(job.normalized_role for job in jobs)
    strongest_by_role_skill_job: dict[tuple[str, str, int], RequirementType] = {}

    for skill in skills:
        job = jobs_by_id.get(skill.job_id)
        if job is None:
            continue
        key = (job.normalized_role, skill.normalized_skill, skill.job_id)
        current = strongest_by_role_skill_job.get(key)
        if current is None or REQUIREMENT_RANK[skill.requirement_type] > REQUIREMENT_RANK[current]:
            strongest_by_role_skill_job[key] = skill.requirement_type

    counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for (role, skill_name, _job_id), requirement_type in strongest_by_role_skill_job.items():
        counts[(role, skill_name)][requirement_type] += 1

    stats: list[SkillStat] = []
    for (role, skill_name), requirement_counts in sorted(counts.items()):
        role_total = role_job_counts[role]
        skill_job_total = sum(requirement_counts.values())
        percentage = round((skill_job_total / role_total) * 100, 2) if role_total else 0.0
        stats.append(
            SkillStat(
                normalized_role=role,
                skill=skill_name,
                job_count=role_total,
                required_count=requirement_counts["required"],
                preferred_count=requirement_counts["preferred"],
                nice_to_have_count=requirement_counts["nice_to_have"],
                mentioned_count=requirement_counts["mentioned"],
                percentage=percentage,
            )
        )
    return stats
