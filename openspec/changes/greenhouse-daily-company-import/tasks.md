## 1. Configuration and Filtering

- [x] 1.1 Add fixture-based tests for loading valid Greenhouse company JSON with enabled companies, target roles, excluded title keywords, and language filters.
- [x] 1.2 Add tests that malformed company JSON or missing required company fields fail before any network request is attempted.
- [x] 1.3 Implement Greenhouse company-list data structures and a loader for a user-supplied JSON file.
- [x] 1.4 Implement local target-role filtering over title, department names, language, and excluded title keywords.
- [x] 1.5 Add tests proving matching jobs receive the configured `normalized_role` and non-target jobs are excluded by default.

## 2. Greenhouse Adapter

- [x] 2.1 Add Greenhouse API response fixtures covering valid jobs, missing `absolute_url`, missing content, departments, locations, language, and prospect posts.
- [x] 2.2 Implement the Greenhouse public jobs URL with `content=true` for configured board tokens.
- [x] 2.3 Implement a small HTTP fetch boundary with timeout and transparent user agent, using the Python standard library unless a dependency is explicitly justified.
- [x] 2.4 Map accepted Greenhouse records into shared `JobPosting` objects with source `greenhouse`, company from config, stable source URL, title, location, description text, and normalized role.
- [x] 2.5 Skip and report records without usable description content after cleanup.
- [x] 2.6 Add tests proving the adapter does not call non-public, login-required, application, generic career-page, or bypass-oriented paths.

## 3. Daily Snapshot Persistence

- [x] 3.1 Add database tests for inserting first-seen Greenhouse jobs with local `first_seen_at` and `last_seen_at` values.
- [x] 3.2 Add database tests proving repeated imports update `last_seen_at` without inserting duplicate jobs.
- [x] 3.3 Extend the database boundary with an upsert/save path that preserves source URL and description-hash deduplication while updating seen timestamps for existing jobs.
- [x] 3.4 Confirm existing manual import and analytics tests still pass with the updated database behavior.

## 4. CLI Import Flow

- [x] 4.1 Add CLI tests for a Greenhouse import command that accepts a company JSON file and database path.
- [x] 4.2 Implement the Greenhouse daily import command to load config, fetch enabled companies, apply filters, save matching jobs, and print an import summary.
- [x] 4.3 Ensure per-company request failures are collected and reported while remaining enabled companies continue processing.
- [x] 4.4 Ensure malformed configuration fails fast and returns a non-zero CLI result before network calls.

## 5. Sample Data and Documentation

- [x] 5.1 Add a repository-safe sample Greenhouse company JSON file with clearly editable company entries and target role filters.
- [x] 5.2 Update README usage examples to show the Greenhouse daily import command and clarify curated-board snapshot semantics.
- [x] 5.3 Document that Greenhouse `updated_at` is not treated as a guaranteed original posting date.
- [x] 5.4 Document that raw job descriptions are local extraction inputs and are not included in public stats exports.

## 6. Verification

- [x] 6.1 Run the full pytest suite.
- [x] 6.2 Run a local CLI smoke test against a temporary SQLite database using fixture/manual-safe inputs.
- [x] 6.3 Run OpenSpec validation for `greenhouse-daily-company-import`.
- [x] 6.4 Review the implementation diff for compliance with the prohibited-source and no-bypass constraints before committing or opening a PR.
