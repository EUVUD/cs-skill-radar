## Why

CS Skill Radar needs a clear backend-first project structure before implementation begins. The repository is currently empty, and an explicit structure will keep the MVP focused on a compliant, testable data pipeline instead of drifting into risky scraping or premature frontend work.

## What Changes

- Define a Python package layout for the CS Skill Radar MVP.
- Separate source adapters, shared models, storage, extraction, analytics, exports, compliance helpers, and CLI entrypoints into distinct modules.
- Establish boundaries for allowed data collection sources: public Greenhouse, Lever, Ashby APIs and manual user-provided input.
- Include a test layout that covers normalization, deduplication, analytics, and adapter behavior.
- Include data and export directories for local samples and generated artifacts.
- Leave frontend, FastAPI, PostgreSQL, LLM extraction, and generic career-page crawling as later extensions.

## Capabilities

### New Capabilities

- `project-structure`: Defines the repository layout, module responsibilities, dependency boundaries, and test/data organization for the initial backend data pipeline.

### Modified Capabilities

None.

## Impact

- Affected code: future `src/cs_skill_radar/` package, CLI module, tests, sample data, and export directories.
- Affected dependencies: Python packaging metadata, Pydantic, SQLite access, HTTP client, optional HTML cleanup utilities, and pytest.
- Affected systems: local developer workflow, local SQLite database, local JSON/CSV exports.
- Compliance impact: default source collection remains limited to public APIs and manual input; high-risk scraping sources remain out of scope.
