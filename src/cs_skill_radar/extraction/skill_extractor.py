"""Provider-neutral skill extraction interface."""

from __future__ import annotations

import re
from dataclasses import dataclass

from cs_skill_radar.extraction.requirement_classifier import classify_requirement_context
from cs_skill_radar.extraction.skill_normalizer import normalize_skill
from cs_skill_radar.models import ExtractedSkill, RequirementType

SKILL_ALIASES: tuple[str, ...] = (
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "Go",
    "C++",
    "C#",
    "Ruby",
    "Rust",
    "Kotlin",
    "Swift",
    "REST API",
    "GraphQL",
    "FastAPI",
    "Django",
    "Flask",
    "Spring Boot",
    "Node",
    "Node.js",
    "Express",
    "React",
    "React.js",
    "Next.js",
    "Vue",
    "Angular",
    "HTML",
    "CSS",
    "Tailwind CSS",
    "Postgres",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Redis",
    "Elasticsearch",
    "AWS",
    "Amazon Web Services",
    "GCP",
    "Azure",
    "Docker",
    "Kubernetes",
    "K8s",
    "Terraform",
    "CI/CD",
    "GitHub Actions",
    "PyTorch",
    "TensorFlow",
    "scikit-learn",
    "Pandas",
    "NumPy",
    "Spark",
    "LLMs",
    "Large Language Models",
    "RAG",
    "vector database",
    "LangChain",
    "LangGraph",
    "OpenAI API",
    "Claude API",
    "prompt engineering",
    "evaluation",
    "distributed systems",
    "microservices",
    "observability",
    "monitoring",
    "Kafka",
    "RabbitMQ",
)

REQUIREMENT_RANK: dict[RequirementType, int] = {
    "mentioned": 0,
    "nice_to_have": 1,
    "preferred": 2,
    "required": 3,
}


@dataclass(frozen=True)
class RuleBasedSkillExtractor:
    aliases: tuple[str, ...] = SKILL_ALIASES

    def extract(self, description: str, job_id: int | None = None) -> list[ExtractedSkill]:
        found: dict[str, ExtractedSkill] = {}
        for alias in self.aliases:
            for match in _iter_skill_matches(description, alias):
                normalized = normalize_skill(alias)
                context = _context_window(description, match.start(), match.end())
                requirement_type = classify_requirement_context(context)
                candidate = ExtractedSkill(
                    job_id=job_id or 0,
                    raw_skill=match.group(0),
                    normalized_skill=normalized,
                    requirement_type=requirement_type,
                    confidence=0.9,
                )
                current = found.get(normalized)
                if current is None or REQUIREMENT_RANK[candidate.requirement_type] > REQUIREMENT_RANK[current.requirement_type]:
                    found[normalized] = candidate
        return list(found.values())


def extract_skills(description: str, job_id: int | None = None) -> list[ExtractedSkill]:
    return RuleBasedSkillExtractor().extract(description, job_id=job_id)


def _iter_skill_matches(description: str, alias: str) -> list[re.Match[str]]:
    escaped = re.escape(alias)
    pattern = rf"(?<![A-Za-z0-9+#]){escaped}(?![A-Za-z0-9+#])"
    return list(re.finditer(pattern, description, flags=re.IGNORECASE))


def _context_window(description: str, start: int, end: int, size: int = 80) -> str:
    return description[max(0, start - size) : min(len(description), end + size)]
