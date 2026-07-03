## 1. Repository Scaffold

- [x] 1.1 Create `README.md`, `pyproject.toml`, and `.gitignore` for a Python package named `cs-skill-radar`.
- [x] 1.2 Create the `src/cs_skill_radar/` package with `__init__.py`, `models.py`, `db.py`, `config.py`, and `cli.py`.
- [x] 1.3 Create package subdirectories for `sources/`, `extraction/`, `analytics/`, and `compliance/`, each with `__init__.py`.
- [x] 1.4 Create `tests/`, `data/`, and `exports/` directories with repository-safe placeholder or sample files where needed.

## 2. Domain Models and Storage

- [x] 2.1 Define Pydantic models for `JobPosting`, `ExtractedSkill`, and `SkillStat` with the fields required by the spec.
- [x] 2.2 Implement description hashing and normalized deduplication fields for job postings.
- [x] 2.3 Implement a small SQLite database layer behind `db.py` for initializing tables, saving jobs, detecting duplicates, saving extracted skills, and reading analytics inputs.
- [x] 2.4 Keep database details isolated so source adapters, extraction, analytics, and exports use project-level functions or classes instead of raw SQL.

## 3. Source and Compliance Boundaries

- [x] 3.1 Define a source adapter interface in `sources/base.py` that returns normalized `JobPosting` objects.
- [x] 3.2 Implement `sources/manual.py` to load user-provided JSON job data without network access.
- [x] 3.3 Add Greenhouse, Lever, and Ashby adapter modules as clearly bounded public-API adapter locations without implementing high-risk scraping behavior.
- [x] 3.4 Implement compliance helpers for denied source names, default allowed source categories, basic rate-limit structure, and future robots.txt checks.
- [x] 3.5 Ensure LinkedIn, Indeed, Glassdoor, login-required scraping, anti-bot bypass, proxy rotation, and stealth scraping are not implemented as default adapters.

## 4. Extraction Pipeline

- [x] 4.1 Implement a rule-based skill normalizer with canonical mappings for common aliases such as `Postgres`, `K8s`, `Node`, `React.js`, and `Amazon Web Services`.
- [x] 4.2 Implement requirement classification for `required`, `preferred`, `nice_to_have`, and `mentioned` contexts.
- [x] 4.3 Implement a provider-neutral skill extractor interface that returns structured `ExtractedSkill` records.
- [x] 4.4 Keep the first extractor rule-based while preserving a clean path for a later LLM-backed extractor.

## 5. Analytics, Exports, and CLI

- [x] 5.1 Implement role-level skill statistics that count each normalized skill at most once per job posting.
- [x] 5.2 Include job count, percentage, required count, preferred count, nice-to-have count, and mentioned count in computed stats.
- [x] 5.3 Implement JSON and CSV export functions for computed skill statistics.
- [x] 5.4 Add CLI entrypoints for manual import, skill extraction, stats computation, and JSON/CSV export.
- [x] 5.5 Keep frontend, FastAPI, PostgreSQL, generic career-page crawling, and LLM extraction out of the initial implementation.

## 6. Tests and Sample Data

- [x] 6.1 Add sample manual job data in `data/sample_jobs.json`.
- [x] 6.2 Add tests for skill alias normalization.
- [x] 6.3 Add tests for database-level job deduplication by source URL or description hash.
- [x] 6.4 Add tests proving repeated skill mentions within one job count once in analytics.
- [x] 6.5 Add tests for the manual adapter returning normalized `JobPosting` objects.
- [x] 6.6 Run the test suite and update documentation with the verified local commands.
