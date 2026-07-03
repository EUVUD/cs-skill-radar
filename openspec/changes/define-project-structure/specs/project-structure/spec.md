## ADDED Requirements

### Requirement: Backend-first Python package layout

The project SHALL define a backend-first Python package layout under `src/cs_skill_radar/` with separate modules for models, database access, configuration, CLI commands, source adapters, extraction, analytics, exports, and compliance helpers.

#### Scenario: Project scaffold is inspectable

- **WHEN** a developer opens the repository after implementation
- **THEN** the repository contains `src/cs_skill_radar/`, `tests/`, `data/`, and `exports/` paths with responsibilities matching the project design

#### Scenario: Package imports use the src layout

- **WHEN** tests import project code
- **THEN** imports resolve through the installed `cs_skill_radar` package instead of relying on accidental local-path imports

### Requirement: Source adapters produce shared job postings

The project SHALL isolate source-specific collection in `sources/` adapters that produce shared `JobPosting` objects for downstream storage, extraction, and analytics.

#### Scenario: Manual input adapter normalizes user-provided jobs

- **WHEN** a developer imports manual JSON job data
- **THEN** the manual adapter returns normalized `JobPosting` objects without requiring network access

#### Scenario: API adapters remain source-specific

- **WHEN** Greenhouse, Lever, or Ashby adapter code is added
- **THEN** each adapter handles only source-specific retrieval and mapping before returning shared `JobPosting` objects

### Requirement: Domain models define pipeline contracts

The project SHALL define structured domain models for `JobPosting`, `ExtractedSkill`, and `SkillStat` so adapters, storage, extraction, analytics, and exports exchange validated data shapes.

#### Scenario: Job posting model captures deduplication fields

- **WHEN** a `JobPosting` is created
- **THEN** it includes source, source URL, title, company, normalized role, description, and description hash fields needed for collection and deduplication

#### Scenario: Extracted skill model captures requirement type

- **WHEN** a skill is extracted from a job description
- **THEN** the extracted record includes raw skill, normalized skill, requirement type, and confidence

### Requirement: Persistence is behind a database boundary

The project SHALL keep SQLite persistence details behind `db.py` or an equivalent database module so adapters, extraction, analytics, and CLI code do not depend on raw storage details.

#### Scenario: Duplicate jobs are detected by stable identifiers

- **WHEN** the same job is imported more than once with the same source URL or normalized description hash
- **THEN** the database layer prevents duplicate job records from being counted as separate postings

#### Scenario: Storage implementation can evolve

- **WHEN** PostgreSQL support is considered later
- **THEN** most adapter, extraction, analytics, and export code can remain unchanged because persistence details are isolated

### Requirement: Extraction is provider-neutral

The project SHALL separate skill normalization, requirement classification, and extraction orchestration so the first rule-based extractor can later be replaced or augmented by an LLM-based extractor.

#### Scenario: Skill aliases normalize to canonical names

- **WHEN** extracted text includes aliases such as `Postgres`, `K8s`, `React.js`, or `Amazon Web Services`
- **THEN** the normalizer returns canonical names such as `PostgreSQL`, `Kubernetes`, `React`, or `AWS`

#### Scenario: Extractor returns structured skill records

- **WHEN** the extractor processes a job description
- **THEN** it returns structured `ExtractedSkill` records rather than provider-specific free-form text

### Requirement: Analytics count a skill once per job

The project SHALL compute role-level skill statistics so each normalized skill contributes at most one job-level frequency count per job posting.

#### Scenario: Repeated mentions do not inflate frequency

- **WHEN** a job description mentions `Python` multiple times
- **THEN** analytics count that job once for the `Python` skill frequency

#### Scenario: Stats include requirement-type counts

- **WHEN** analytics are computed for a normalized role
- **THEN** the result includes job count, skill frequency percentage, and required, preferred, nice-to-have, and mentioned counts

### Requirement: Exports are generated from analytics outputs

The project SHALL provide JSON and CSV export paths for computed skill statistics without requiring a frontend.

#### Scenario: JSON stats export is available

- **WHEN** a developer requests a JSON stats export
- **THEN** the project writes role-level skill statistics in a JSON-compatible structure

#### Scenario: CSV stats export is available

- **WHEN** a developer requests a CSV stats export
- **THEN** the project writes role-level skill statistics in tabular CSV form

### Requirement: Compliance boundaries are explicit

The project SHALL include compliance helpers and source boundaries that keep default collection limited to public job-board APIs and manual user-provided input.

#### Scenario: High-risk sources are not default adapters

- **WHEN** a developer reviews available source adapters
- **THEN** LinkedIn, Indeed, Glassdoor, login-required scraping, anti-bot bypass, proxy rotation, and stealth scraping are absent from default adapters

#### Scenario: Generic career-page crawling is excluded from the MVP

- **WHEN** the initial project structure is implemented
- **THEN** generic company career-page crawling is not enabled as a default collection path

### Requirement: Tests cover core pipeline behavior

The project SHALL include tests for skill normalization, per-job deduplication, analytics frequency counting, and manual adapter behavior.

#### Scenario: Normalization tests cover common aliases

- **WHEN** tests run for the skill normalizer
- **THEN** they verify canonical mappings for representative aliases such as `Postgres`, `K8s`, `Node`, and `React.js`

#### Scenario: Analytics tests cover per-job deduplication

- **WHEN** tests run for analytics
- **THEN** they verify repeated skill mentions within a single job do not count as multiple job-level skill occurrences
