## ADDED Requirements

### Requirement: Curated Greenhouse company configuration

The system SHALL load Greenhouse import targets from a user-modifiable JSON configuration file containing enabled company entries, board tokens, company names, and local role-filter rules.

#### Scenario: Load enabled company entries
- **WHEN** the Greenhouse daily import is started with a valid company configuration file
- **THEN** the system loads only enabled company entries with non-empty company names and board tokens

#### Scenario: Reject malformed company configuration
- **WHEN** the company configuration file is missing required fields or has invalid JSON
- **THEN** the system fails before making Greenhouse API requests and reports the configuration problem

#### Scenario: Support configurable target roles
- **WHEN** the company configuration includes target role definitions with normalized role names and keyword filters
- **THEN** the import uses those definitions to decide which Greenhouse jobs are relevant to the configured positions

### Requirement: Public Greenhouse job board retrieval

The system SHALL retrieve Greenhouse jobs only through documented public Job Board API GET endpoints for explicitly configured board tokens.

#### Scenario: Fetch board jobs with content
- **WHEN** the importer processes an enabled company with board token `example`
- **THEN** it requests the public jobs endpoint for that board with `content=true`

#### Scenario: Do not use prohibited collection behavior
- **WHEN** the Greenhouse importer collects jobs
- **THEN** it does not use login-required scraping, browser automation, CAPTCHA or Cloudflare bypass, anti-bot bypass, proxy rotation, stealth scraping, or generic career-page crawling

#### Scenario: Continue after one company fetch fails
- **WHEN** one enabled company board request fails but other enabled companies remain
- **THEN** the daily import records the failure, continues with remaining companies, and reports a summary of successful and failed companies

### Requirement: Greenhouse payload mapping

The system SHALL map accepted Greenhouse job records into shared `JobPosting` objects for downstream storage, extraction, analytics, and exports.

#### Scenario: Map a valid Greenhouse job
- **WHEN** a Greenhouse job record includes a title, absolute URL, location, content, and company from configuration
- **THEN** the importer returns a `JobPosting` with source `greenhouse`, source URL from the Greenhouse absolute URL, company from configuration, title from the job record, location from the job record, and description from the job content

#### Scenario: Use stable fallback source URL
- **WHEN** a Greenhouse job record has a valid job id but no absolute URL
- **THEN** the importer creates a stable Greenhouse source URL from the board token and job id

#### Scenario: Skip records without usable descriptions
- **WHEN** a Greenhouse job record lacks usable description content after text cleanup
- **THEN** the importer does not create a `JobPosting` for that record and reports that the record was skipped

### Requirement: Local position filtering

The system SHALL apply local position filters to Greenhouse jobs so daily imports can target specific software engineering roles without relying on unsupported Greenhouse server-side search.

#### Scenario: Include matching target role
- **WHEN** a job title or department matches a configured target role rule
- **THEN** the importer includes the job and assigns the configured normalized role to the resulting `JobPosting`

#### Scenario: Exclude non-target positions
- **WHEN** a job matches an excluded title keyword or matches no configured target role
- **THEN** the default daily import excludes that job from storage

#### Scenario: Filter by language
- **WHEN** the company configuration restricts accepted languages
- **THEN** the importer excludes Greenhouse jobs whose language is not in the configured language list

### Requirement: Daily snapshot import semantics

The system SHALL treat a daily Greenhouse import as a local snapshot run over configured boards, preserving existing deduplication and updating local seen timestamps for jobs observed again.

#### Scenario: Insert first-seen job
- **WHEN** a matching Greenhouse job has not been saved before by source URL or description hash
- **THEN** the database stores it as a new job with `first_seen_at` and `last_seen_at` representing the local import time

#### Scenario: Update seen timestamp for existing job
- **WHEN** a matching Greenhouse job has already been saved by source URL or description hash
- **THEN** the database does not insert a duplicate job and updates the existing job's `last_seen_at` for the current import run

#### Scenario: Avoid source posted-date claims
- **WHEN** a Greenhouse job includes `updated_at`
- **THEN** the system does not treat that value as a guaranteed original posting date for daily-new-job reporting

### Requirement: Greenhouse import CLI

The system SHALL provide a CLI command for running the Greenhouse daily import from a JSON company configuration file.

#### Scenario: Import from configured company list
- **WHEN** a developer runs the Greenhouse import CLI command with a company configuration file and database path
- **THEN** the command loads the configured companies, fetches public Greenhouse jobs, applies local filters, saves matching jobs, and prints an import summary

#### Scenario: Preserve downstream pipeline compatibility
- **WHEN** Greenhouse jobs are imported through the CLI
- **THEN** the existing skill extraction, analytics, and export commands can operate on those jobs without Greenhouse-specific handling

### Requirement: Raw description redistribution boundary

The system SHALL use Greenhouse job descriptions as local extraction inputs without adding public exports of full raw job descriptions.

#### Scenario: Export aggregate stats only
- **WHEN** a developer exports skill statistics after Greenhouse imports
- **THEN** the existing JSON and CSV stats exports contain aggregated skill statistics rather than full raw Greenhouse job descriptions
