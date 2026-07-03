"""Denied and allowed source categories."""

from __future__ import annotations

DENIED_SOURCES = {
    "linkedin",
    "indeed",
    "glassdoor",
    "login_required",
    "captcha_bypass",
    "cloudflare_bypass",
    "anti_bot_bypass",
    "proxy_rotation",
    "stealth_scraping",
}

ALLOWED_DEFAULT_SOURCES = {
    "manual",
    "greenhouse",
    "lever",
    "ashby",
}


def normalize_source_name(source: str) -> str:
    return source.strip().lower().replace(" ", "_").replace("-", "_")


def is_denied_source(source: str) -> bool:
    return normalize_source_name(source) in DENIED_SOURCES


def is_allowed_default_source(source: str) -> bool:
    return normalize_source_name(source) in ALLOWED_DEFAULT_SOURCES


def assert_allowed_default_source(source: str) -> None:
    if is_denied_source(source) or not is_allowed_default_source(source):
        raise ValueError(f"source is not allowed by default: {source}")
