"""Domain models for the CS Skill Radar pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RequirementType = Literal["required", "preferred", "nice_to_have", "mentioned"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_description_text(description: str) -> str:
    return " ".join(description.split()).strip().lower()


def compute_description_hash(description: str) -> str:
    normalized = normalize_description_text(description)
    return sha256(normalized.encode("utf-8")).hexdigest()


class JobPosting(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: int | None = None
    source: str
    source_url: str
    company: str
    title: str
    normalized_role: str = "unknown"
    location: str | None = None
    seniority: str | None = None
    description: str
    description_hash: str | None = None
    first_seen_at: datetime = Field(default_factory=utc_now)
    last_seen_at: datetime = Field(default_factory=utc_now)

    @field_validator("source", "source_url", "company", "title", "normalized_role")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be blank")
        return cleaned

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("description must not be blank")
        return cleaned

    @model_validator(mode="after")
    def ensure_description_hash(self) -> JobPosting:
        object.__setattr__(
            self,
            "description_hash",
            self.description_hash or compute_description_hash(self.description),
        )
        return self


class ExtractedSkill(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: int | None = None
    job_id: int
    raw_skill: str
    normalized_skill: str
    requirement_type: RequirementType = "mentioned"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @field_validator("raw_skill", "normalized_skill")
    @classmethod
    def strip_skill_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("skill text must not be blank")
        return cleaned


class SkillStat(BaseModel):
    normalized_role: str
    skill: str
    job_count: int
    required_count: int = 0
    preferred_count: int = 0
    nice_to_have_count: int = 0
    mentioned_count: int = 0
    percentage: float
    time_window: str = "all_time"
