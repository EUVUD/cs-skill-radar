## Context

CS Skill Radar currently has a working backend pipeline for manual JSON input, SQLite persistence, rule-based skill extraction, analytics, and exports. Greenhouse, Lever, and Ashby source modules exist as safe placeholders; `GreenhouseAdapter.collect()` is not implemented yet. The existing project-structure spec requires source adapters to return shared `JobPosting` objects and keeps default collection limited to public APIs and manual input.

The Greenhouse public Job Board API exposes published jobs by company board token, including job content when `content=true` is requested. It does not provide a global search endpoint or reliable "all jobs posted today across Greenhouse" feed. Daily collection therefore needs to mean "run a snapshot import for a curated set of boards and record what was first seen or seen again locally."

Compliance is central. The adapter must use documented public GET endpoints only. It must not fetch LinkedIn, Indeed, Glassdoor, login-required pages, application submission endpoints, protected pages, generic career pages, or any anti-bot/bypass path.

## Goals / Non-Goals

**Goals:**

- Implement a Greenhouse public API adapter that fetches current public jobs from configured company board tokens.
- Store the curated source universe in a user-modifiable JSON file.
- Support daily import runs from that JSON list while preserving deduplication.
- Filter imported jobs toward software-engineering-oriented positions using local, configurable rules.
- Map Greenhouse payloads into existing `JobPosting` objects without leaking source-specific structures downstream.
- Preserve a compliance-friendly story: public API only, no scraping/bypass, and no public raw job-description redistribution.
- Add deterministic tests with fixture payloads rather than tests that depend on live Greenhouse boards.

**Non-Goals:**

- Building a global Greenhouse crawler, board discovery system, or market-wide "all jobs today" feed.
- Adding LinkedIn, Indeed, Glassdoor, generic career-page crawling, or login-required sources.
- Submitting applications or calling Greenhouse application endpoints.
- Adding proxy rotation, CAPTCHA handling, Cloudflare bypass, browser automation, or stealth scraping.
- Building the future dashboard or frontend.
- Adding a new external HTTP dependency unless implementation proves the standard library is inadequate.

## Decisions

### Decision: Store curated Greenhouse companies in JSON

Use a JSON file for the curated company list because it is easy to review, edit, version-control, and override from the CLI. The implementation should support a sample/default file in `data/` and a CLI option for user-provided files.

Representative shape:

```json
{
  "companies": [
    {
      "name": "ExampleCloud",
      "board_token": "examplecloud",
      "enabled": true,
      "homepage": "https://boards.greenhouse.io/examplecloud"
    }
  ],
  "target_roles": [
    {
      "normalized_role": "backend_engineer",
      "title_keywords": ["backend", "software engineer", "platform engineer"],
      "department_keywords": ["engineering", "r&d"]
    }
  ],
  "exclude_title_keywords": ["sales", "recruiter", "marketing"],
  "languages": ["en"]
}
```

Company entries are the auditable source boundary. Role filters are local heuristics, not Greenhouse API parameters.

Alternative considered: hard-code board tokens in Python. That would be simpler initially but makes the source universe opaque and requires code changes for normal data curation.

### Decision: Keep Greenhouse retrieval source-specific and thin

`GreenhouseAdapter` should be responsible for building the documented API URL, fetching JSON, validating the broad response shape, and mapping each accepted job into `JobPosting`. It should not compute analytics, extract skills, write exports, or discover new companies.

The adapter should request:

```text
GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
```

It should use a timeout, a transparent user agent identifying the open-source tool, and the existing rate-limiter pattern if multiple companies are fetched in one run.

Alternative considered: retrieve each job detail individually. The list endpoint with `content=true` already includes descriptions, departments, and offices, so per-job requests would add avoidable API traffic.

### Decision: Treat daily imports as local snapshots

The system should fetch all current jobs for each enabled company during a run, apply local filters, and save matching jobs. New jobs are identified by first insertion time. Existing jobs should update `last_seen_at` so a daily run can answer "seen during this run/day" without creating duplicates.

The system should not infer that a job was created on the Greenhouse `updated_at` date. Source `updated_at` may represent edits, not original publication. If source update metadata is needed later, it can be added as source metadata or a dedicated field in a later change.

Alternative considered: implement `updated_at >= today` filtering as the definition of daily data. That would miss older-but-still-open jobs first observed today and overstate edited jobs as newly posted.

### Decision: Filter locally by target role rules

Filtering should happen after API retrieval because the Greenhouse list jobs endpoint does not provide documented title, department, or date filters. The first implementation should support straightforward keyword rules over job title, department names, language, and optional exclude keywords.

When a job matches a configured target role, the adapter/import path should set `normalized_role` to that role. If a job matches no target role, the default daily import should skip it unless the config or CLI explicitly requests unmatched jobs.

Alternative considered: use the existing skill extractor to decide whether a job is relevant. Skill extraction is useful after import, but position relevance should be decided before storage to keep the corpus focused and avoid importing unrelated jobs with incidental technical terms.

### Decision: Store raw descriptions locally but keep exports clean

`JobPosting.description` remains the local extraction input. The importer may store the Greenhouse `content` field as cleaned plain text in SQLite. Public export commands should continue exporting aggregated skill stats, not full raw job descriptions.

Alternative considered: store only description hashes and fetch descriptions later. That would reduce local data but break the current extraction pipeline and make repeatability worse.

### Decision: Continue on per-company failures with a visible summary

A daily run across many companies should not fail entirely because one board token is invalid or temporarily unavailable. The import command should collect successes and failures, continue to the next enabled company, and print a summary that makes failed companies visible. Malformed configuration should fail fast before network calls.

Alternative considered: abort on first company failure. That is simpler but makes scheduled daily imports fragile.

## Risks / Trade-offs

- Greenhouse has no global feed → The project must describe coverage as curated-board snapshots, not complete market-wide daily data.
- `updated_at` is not the same as posted date → Use local `first_seen_at`/`last_seen_at` semantics and avoid claiming source creation dates.
- Keyword role filters can be noisy → Keep filters configurable and tested with representative fixtures; allow users to adjust JSON without code changes.
- Some boards may omit content or use unusual HTML → Clean descriptions conservatively and skip/flag jobs that cannot produce a valid `JobPosting`.
- A large curated list could generate many requests → Keep one list request per enabled company, add a small delay/rate limiter, and avoid per-job fetches.
- Raw descriptions are stored locally for extraction → Keep public exports aggregated and document that raw descriptions are not redistributed.

## Migration Plan

1. Add the Greenhouse company-list loader and validated data structures.
2. Implement the Greenhouse adapter using fixture-driven tests for payload mapping.
3. Add local target-role filtering and tests for include/exclude behavior.
4. Extend the database save/upsert boundary so existing jobs update `last_seen_at` without duplicate inserts.
5. Add the CLI import command for daily Greenhouse collection from the JSON company file.
6. Add sample company-list JSON and README usage notes.
7. Run the existing test suite plus new Greenhouse tests and a local CLI smoke test using fixtures or a temporary database.

Rollback is straightforward before release: remove the new change files or revert the implementation commit. Database changes should be additive and backward-compatible; if `last_seen_at` update behavior is changed in code only, no schema rollback is needed.

## Open Questions

- What should the default sample company list contain: fictional examples only, a very small real curated list, or no enabled companies by default?
- Should unmatched jobs be skipped by default with an explicit `include_unmatched` option, or imported as `normalized_role="unknown"` for later manual review?
- Should source `updated_at` be stored in this change, or deferred until the project has a broader source-metadata model?
