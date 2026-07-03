"""Requirement type classification."""

from __future__ import annotations

from cs_skill_radar.models import RequirementType

REQUIRED_MARKERS = (
    "required",
    "must have",
    "must-have",
    "need",
    "needs",
    "experience with",
    "proficiency in",
)
PREFERRED_MARKERS = (
    "preferred",
    "nice to have",
    "nice-to-have",
    "bonus",
    "plus",
    "would be great",
)
NICE_TO_HAVE_MARKERS = ("nice to have", "nice-to-have", "bonus")


def classify_requirement_context(text: str) -> RequirementType:
    lowered = text.lower()
    if any(marker in lowered for marker in NICE_TO_HAVE_MARKERS):
        return "nice_to_have"
    if any(marker in lowered for marker in PREFERRED_MARKERS):
        return "preferred"
    if any(marker in lowered for marker in REQUIRED_MARKERS):
        return "required"
    return "mentioned"
