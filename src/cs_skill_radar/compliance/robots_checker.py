"""Future robots.txt checking boundary."""

from __future__ import annotations


def generic_crawling_requires_robots_check() -> bool:
    return True


def assert_generic_crawling_disabled() -> None:
    raise NotImplementedError("Generic career-page crawling is intentionally disabled for the MVP.")
