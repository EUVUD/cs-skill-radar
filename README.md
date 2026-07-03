# CS Skill Radar

CS Skill Radar is a backend-first Python project for collecting public software engineering job postings, extracting technical skills, and computing role-level skill demand statistics.

The project is intentionally focused on a compliant data pipeline. Default collection targets public job-board APIs and user-provided job descriptions only. It does not implement LinkedIn, Indeed, Glassdoor, login-required scraping, CAPTCHA bypass, anti-bot bypass, proxy rotation, or stealth scraping.

## MVP Pipeline

```text
manual/public API source -> JobPosting -> SQLite -> ExtractedSkill -> SkillStat -> JSON/CSV export
```

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest
```

## CLI Examples

```bash
cs-skill-radar import-manual --file data/sample_jobs.json
cs-skill-radar extract-skills
cs-skill-radar compute-stats
cs-skill-radar export-stats --format json
cs-skill-radar export-stats --format csv
```

## Verification

```bash
.venv/bin/python -m pytest
.venv/bin/cs-skill-radar --db /private/tmp/cs_skill_radar_smoke.sqlite import-manual --file data/sample_jobs.json
.venv/bin/cs-skill-radar --db /private/tmp/cs_skill_radar_smoke.sqlite extract-skills
.venv/bin/cs-skill-radar --db /private/tmp/cs_skill_radar_smoke.sqlite compute-stats
.venv/bin/cs-skill-radar --db /private/tmp/cs_skill_radar_smoke.sqlite export-stats --format json --output /private/tmp/cs_skill_radar_stats.json
.venv/bin/cs-skill-radar --db /private/tmp/cs_skill_radar_smoke.sqlite export-stats --format csv --output /private/tmp/cs_skill_radar_stats.csv
```
