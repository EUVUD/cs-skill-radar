"""Skill alias normalization."""

from __future__ import annotations

ALIASES: dict[str, str] = {
    "amazon web services": "AWS",
    "aws": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "azure": "Azure",
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "large language models": "LLMs",
    "large language model": "LLMs",
    "llm": "LLMs",
    "llms": "LLMs",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "github actions": "GitHub Actions",
    "rest api": "REST API",
    "rest apis": "REST API",
    "openai api": "OpenAI API",
    "claude api": "Claude API",
    "vector db": "vector database",
    "vector databases": "vector database",
}


def normalize_skill(raw_skill: str) -> str:
    cleaned = " ".join(raw_skill.strip().split())
    return ALIASES.get(cleaned.lower(), cleaned)
