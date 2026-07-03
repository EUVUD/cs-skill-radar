## Why

CS Skill Radar needs its first real public API source so the pipeline can collect useful market data without relying only on manual JSON input. Greenhouse is a good fit because its public Job Board API exposes published job data by company board token without authentication, while still keeping the project away from high-risk scraping.

The project also needs a repeatable way to collect daily snapshots from a curated set of companies. A modifiable local company list keeps the source universe explicit, auditable, and easy to adjust without code changes.

## What Changes

- Implement the Greenhouse public Job Board API adapter so it fetches published jobs from configured company board tokens using documented public GET endpoints only.
- Add a JSON-based company configuration file that lists curated Greenhouse board tokens and company metadata.
- Add a daily import path that loads the curated company list, fetches each configured Greenhouse board, maps returned postings into shared `JobPosting` objects, and saves them through the existing database boundary.
- Add local filtering for software-engineering-oriented positions so imported data can be geared toward target roles without relying on unsupported Greenhouse server-side search.
- Treat daily data as a local snapshot concept: the system can identify jobs first seen during a run/day and jobs updated by the source, but it will not claim complete market-wide or globally posted-today coverage.
- Preserve compliance boundaries: no LinkedIn, Indeed, Glassdoor, login-required scraping, CAPTCHA/Cloudflare/anti-bot bypass, proxy rotation, stealth behavior, generic career-page crawling, or public redistribution of full raw job descriptions.

## Capabilities

### New Capabilities

- `greenhouse-daily-import`: Configurable daily import of public Greenhouse job board data from a curated JSON company list, including source mapping, local position filtering, deduplication, and compliant collection boundaries.

### Modified Capabilities

- None.

## Impact

- Affected source modules: `src/cs_skill_radar/sources/greenhouse.py` and likely supporting source/config helpers.
- Affected CLI: add an import command for Greenhouse daily collection from a company config file.
- Affected persistence: may extend the database boundary to update `last_seen_at` for existing jobs and support snapshot-oriented reporting without exposing storage details.
- Affected data files: add a repository-safe sample JSON company list for curated Greenhouse board tokens.
- Affected tests: add deterministic tests for Greenhouse response mapping, company list loading, local filtering, deduplication/update behavior, compliance guardrails, and CLI wiring.
- Dependencies: prefer the Python standard library for HTTP and JSON unless implementation shows a clear need for a small HTTP client dependency.
