## Context

The repository is an empty Python project for CS Skill Radar, an open-source portfolio and learning project. The primary value is a compliant backend data pipeline that collects public software engineering job postings from low-risk sources, extracts technical skills, normalizes them, and produces role-level statistics. The initial website/dashboard is intentionally secondary.

The main constraints are compliance and maintainability. Default collection must be limited to public job-board APIs and user-provided input. The project must not implement LinkedIn, Indeed, Glassdoor, login-required scraping, CAPTCHA or anti-bot bypass, stealth scraping, proxy rotation, or public redistribution of full raw job descriptions.

The planned implementation should make the first MVP useful without overbuilding. Manual input and deterministic rule-based extraction can prove the pipeline before more source adapters, LLM extraction, PostgreSQL, or a frontend are added.

## Goals / Non-Goals

**Goals:**

- Establish a backend-first Python repository structure.
- Keep source collection, normalized models, persistence, extraction, analytics, exports, compliance helpers, and CLI entrypoints separated.
- Make source adapters interchangeable through a common interface.
- Store jobs in SQLite for the MVP while leaving a clean path to PostgreSQL later.
- Support deterministic unit tests for normalization, per-job deduplication, analytics, and adapters.
- Keep high-risk scraping and autonomous web browsing outside the default system.

**Non-Goals:**

- Building a dashboard or website in the initial structure change.
- Adding FastAPI or a public service API.
- Implementing LLM extraction as the first extractor.
- Implementing generic career-page crawling as a default adapter.
- Implementing scraping for LinkedIn, Indeed, Glassdoor, login-required pages, or protected pages.
- Designing a distributed or multi-agent collection system.

## Decisions

### Decision: Use a `src/` Python package layout

The project will use a `src/cs_skill_radar/` package with tests outside the package. This keeps import behavior realistic, avoids accidental local imports, and gives the project a conventional open-source shape.

Target structure:

```text
cs-skill-radar/
├── README.md
├── pyproject.toml
├── .gitignore
├── src/
│   └── cs_skill_radar/
│       ├── __init__.py
│       ├── models.py
│       ├── db.py
│       ├── config.py
│       ├── cli.py
│       ├── sources/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── greenhouse.py
│       │   ├── lever.py
│       │   ├── ashby.py
│       │   └── manual.py
│       ├── extraction/
│       │   ├── __init__.py
│       │   ├── skill_extractor.py
│       │   ├── skill_normalizer.py
│       │   └── requirement_classifier.py
│       ├── analytics/
│       │   ├── __init__.py
│       │   ├── skill_stats.py
│       │   └── exports.py
│       └── compliance/
│           ├── __init__.py
│           ├── denylist.py
│           ├── robots_checker.py
│           └── rate_limiter.py
├── tests/
│   ├── test_skill_normalizer.py
│   ├── test_deduplication.py
│   ├── test_analytics.py
│   └── test_manual_adapter.py
├── data/
│   └── sample_jobs.json
└── exports/
```

Alternative considered: a flat package with fewer directories. That would be faster at the start, but the pipeline has clear domain boundaries; the `src/` structure prevents the first few files from becoming a mixed bag of adapters, database code, and extraction logic.

### Decision: Keep adapters thin and normalize into shared models

Each source adapter will fetch or load source-specific payloads, then return shared `JobPosting` objects. Adapters should not compute analytics, write exports, or embed skill extraction logic. The manual adapter should be the first fully usable adapter because it makes local testing possible without network access.

Alternative considered: storing each source payload as-is and normalizing later. That increases flexibility, but it makes deduplication, extraction, and tests harder in the MVP. The better first boundary is source-specific input in, normalized `JobPosting` out.

### Decision: Use Pydantic models for domain objects

Core domain models will live in `models.py`: `JobPosting`, `ExtractedSkill`, and `SkillStat`. They provide structured validation at adapter and analytics boundaries.

Alternative considered: plain dictionaries or dataclasses. Dictionaries are too loose for a pipeline with several transformation stages. Dataclasses are simple, but Pydantic gives validation and serialization support that will help adapters, imports, and exports.

### Decision: Use a small SQLite database layer behind `db.py`

SQLite will be the first persistence target. The database layer should expose project-level operations such as saving jobs, finding duplicates, saving extracted skills, and reading inputs for analytics. Other modules should not depend on raw SQL details.

Alternative considered: starting with SQLAlchemy. SQLAlchemy is useful if PostgreSQL arrives soon, but a small `sqlite3` layer may be clearer for the MVP. The implementation can choose SQLAlchemy if it stays simple, but the structure should keep persistence behind `db.py` either way.

### Decision: Make extraction provider-neutral

The extraction package will separate three concepts:

- `skill_normalizer.py`: canonicalizes aliases such as `Postgres` to `PostgreSQL`.
- `requirement_classifier.py`: classifies context as required, preferred, nice-to-have, or mentioned.
- `skill_extractor.py`: coordinates extraction and returns structured skill records.

The first implementation should be rule-based with a curated taxonomy. LLM extraction can be added later behind the same structured interface.

Alternative considered: sending every job description to an LLM immediately. That would be flashier, but it raises cost, repeatability, and provider-lock-in concerns before the rest of the pipeline has proven itself.

### Decision: Treat compliance as a first-class module

The compliance package will hold source denylist checks, rate-limit helpers, and future robots.txt support. Default adapters should only target approved public APIs and manual user-provided input. Any generic career-page adapter must remain disabled by default and must perform robots.txt checks and rate limiting.

Alternative considered: putting compliance checks inside each adapter only. Some checks are adapter-specific, but shared guardrails make the project easier to audit and easier to explain publicly.

### Decision: Analytics count a skill at most once per job

The analytics package will calculate role-level skill frequencies from extracted skills. Repeated mentions of the same normalized skill in a single job must count once for job-level frequency statistics, while requirement-type counts should use the strongest or most specific classification available for that skill within that job.

Alternative considered: counting every mention. Mention counts can be interesting later, but they exaggerate long job descriptions and make skill demand look noisier.

## Risks / Trade-offs

- Rule-based extraction misses skills or context → Start with a small explicit taxonomy and focused tests; keep the extractor interface replaceable.
- SQLite schema becomes hard to migrate later → Keep database access behind `db.py` and avoid leaking SQLite-specific details into adapters or analytics.
- Source APIs return inconsistent payloads → Keep adapters isolated and test each adapter's mapping behavior with sample payloads.
- Compliance boundaries become unclear as sources expand → Centralize denylist checks and document allowed default adapters.
- Project structure is too broad for the first implementation → Implement manual import, models, database, normalization, analytics, and tests first; leave network adapters as thin follow-up work if needed.

## Migration Plan

This is the initial repository structure, so no production migration is required. Implementation should create the package layout, metadata files, tests, and sample data in one local change. If the structure proves too broad during implementation, keep the top-level package boundaries but defer incomplete adapters behind clear stubs or task follow-ups rather than mixing responsibilities.

Rollback is simple before public release: remove the created project files or revise the OpenSpec change before applying it.

## Open Questions

No blocking open questions. Initial taxonomy size, exact CLI implementation library, and whether `sqlite3` or SQLAlchemy is used can be decided during implementation as long as the module boundaries and compliance constraints remain intact.
