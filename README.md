# NeraJob

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MergeOS](https://img.shields.io/badge/MergeOS-bounties-5319E7.svg)](https://github.com/mergeos-bounties)

**NeraJob** is a local-first Python toolkit that helps you:

1. **Scan job listings** from public job boards and career APIs (pluggable scrapers)
2. **Build and maintain your CV** from profile data aligned to target roles
3. **Prepare applications** with tailored cover notes, checklists, and export packages

Product source of truth: [mergeos-bounties/NeraJob](https://github.com/mergeos-bounties/NeraJob) under the [mergeos-bounties](https://github.com/mergeos-bounties) organization.

---


## Screenshots

Real captures from running the product demo (NeraJob).

![Scan sample jobs](docs/screenshots/demo-scan-sample.png)

*Scan sample jobs*

![Registered scrapers](docs/screenshots/demo-sources.png)

*Registered scrapers*

![Jobs cache after scan](docs/screenshots/demo-jobs-cache.png)

*Jobs cache after scan*

## Table of contents

- [Features](#features)
- [Supported job sources](#supported-job-sources)
- [Stack](#stack)
- [Quick start](#quick-start)
- [Common commands](#common-commands)
- [Architecture](#architecture)
- [Data layout](#data-layout)
- [Adding a job site](#adding-a-job-site)
- [Compliance](#compliance)
- [Development](#development)
- [MergeOS bounties](#mergeos-bounties-claim-mrg)
- [License](#license)

---

## Features

| Area | What you get |
| --- | --- |
| **Scan** | Query one source or all registered scrapers; results cached in `data/jobs.json` |
| **Profile** | Local JSON profile as CV source of truth |
| **CV** | Markdown + plain-text CV export aimed at a target role |
| **Apply** | Per-job package: cover note, checklist, notes for manual apply |
| **Extensible** | Drop-in scrapers implementing `BaseScraper` + registry |

---

## Supported job sources

Full catalog (API links, env vars, bounty issues): **[docs/SOURCES.md](docs/SOURCES.md)**.

### Shipped (available today)

| `--source` | Site | Type | Network | Auth / config |
| --- | --- | --- | --- | --- |
| `sample` | Built-in demo feed | Offline fixtures | No | None |
| `remoteok` | [RemoteOK](https://remoteok.com) | Public JSON API (`/api`) | Yes | None (polite User-Agent) |
| `remotive` | [Remotive](https://remotive.com) | Public JSON API (`/api/remote-jobs`) | Yes | None. Remote-only board — all jobs are `remote=True`. |
| `arbeitnow` | [Arbeitnow](https://www.arbeitnow.com) | Public JSON API (`/api/job-board-api`) | Yes | None. Conservative pagination; ToS: free for personal/non-commercial. |
| `himalayas` | [Himalayas](https://himalayas.app) | Public JSON API (`/jobs/api`) | Yes | None. Salary metadata, location restrictions. |
| `lever` | [Lever](https://www.lever.co) public postings | Per-company JSON board | Optional | `NERAJOB_LEVER_BOARD` (company slug). Without it: offline sample postings |
| `ashby` | [Ashby](https://www.ashbyhq.com) public job board | Per-company JSON board | Optional | `NERAJOB_ASHBY_BOARD` (board id). Without it: offline sample postings |

```bash
# Offline demo / CI-friendly
nerajob scan --source sample -q python -n 10

# Live remote listings (global feed)
nerajob scan --source remoteok -q "python backend" -n 20
nerajob scan --source remotive -q python -n 20
nerajob scan --source arbeitnow -q python -n 20
nerajob scan --source himalayas -q python -n 20

# Lever / Ashby — set board env for live company boards
set NERAJOB_LEVER_BOARD=netflix
nerajob scan --source lever -q engineer -n 20

set NERAJOB_ASHBY_BOARD=openai
nerajob scan --source ashby -q python -n 20

# Every registered scraper
nerajob scan --all -q python -l remote -n 15
```

| Source detail | Description |
| --- | --- |
| **sample** | Deterministic roles (Python backend, full-stack, platform, ML, automation) for demos and tests. No HTTP. |
| **remoteok** | Live adapter for RemoteOK’s public feed. Client-side keyword filter on title, company, tags, description. On API/network failure returns empty; single-source scan may fall back to `sample`. |
| **remotive** | Live adapter for Remotive’s public API (`https://remotive.com/api/remote-jobs`). All jobs are `remote=True`. Client-side keyword filter. |
| **arbeitnow** | Live adapter for Arbeitnow’s public API (`https://www.arbeitnow.com/api/job-board-api`). EU-focused listings. Client-side keyword filter. |
| **himalayas** | Live adapter for Himalayas.app API (`https://himalayas.app/jobs/api`). Salary metadata, location restrictions. Client-side keyword filter. |
| **lever** | [Lever Postings API](https://github.com/lever/postings-api): `https://api.lever.co/v0/postings/<board>?mode=json`. Board slug via `NERAJOB_LEVER_BOARD`. Missing board → built-in sample row for demos/tests. |
| **ashby** | Ashby public board: `https://api.ashbyhq.com/posting-api/job-board/<board_id>`. Board id via `NERAJOB_ASHBY_BOARD`. Missing board → built-in sample row for demos/tests. |

### Planned (roadmap + open bounties)

Adapters below are **not** in the registry yet. Contribute via open issues labeled `scraper` / `api`.

#### Aggregators & national APIs

| Planned source | Site | Typical access | Issue |
| --- | --- | --- | --- |
| `adzuna` | [Adzuna](https://developer.adzuna.com) | App ID + key | [#7](https://github.com/mergeos-bounties/NeraJob/issues/7) |
| `usajobs` | [USAJOBS](https://developer.usajobs.gov) | Official API | [#8](https://github.com/mergeos-bounties/NeraJob/issues/8) |
| `reed` | [Reed.co.uk](https://www.reed.co.uk/developers) | API key | [#9](https://github.com/mergeos-bounties/NeraJob/issues/9) |
| `themuse` | [The Muse](https://www.themuse.com/developers/api/v2) | Public API | [#10](https://github.com/mergeos-bounties/NeraJob/issues/10) |
| `jooble` | [Jooble](https://jooble.org/api/about) | API key | [#15](https://github.com/mergeos-bounties/NeraJob/issues/15) |

#### Company career boards (ATS)

| Planned source | ATS | Typical access | Issue |
| --- | --- | --- | --- |
| `greenhouse` | [Greenhouse Job Board API](https://developers.greenhouse.io/job-board.html) | Public board JSON | [#11](https://github.com/mergeos-bounties/NeraJob/issues/11) |
| `smartrecruiters` | [SmartRecruiters](https://developers.smartrecruiters.com) | Public postings | [#14](https://github.com/mergeos-bounties/NeraJob/issues/14) |

> **Lever** and **Ashby** are **shipped** (see table above). Remaining ATS boards still planned.

#### Vietnam / regional (ToS-safe only)

| Planned source | Site | Notes | Issue |
| --- | --- | --- | --- |
| `topcv` / `vietnamworks` | TopCV, VietnamWorks | Prefer official / partner APIs; HTML only if ToS-safe | [#17](https://github.com/mergeos-bounties/NeraJob/issues/17) |

#### Scraper platform work

| Work | Issue |
| --- | --- |
| Shared HTTP client, retries, rate limit, robots-aware policy | [#18](https://github.com/mergeos-bounties/NeraJob/issues/18) |
| `scan --all` aggregation + dedupe | [#19](https://github.com/mergeos-bounties/NeraJob/issues/19) |
| Multi-source pack: 5+ live scrapers with CI mocks | [#22](https://github.com/mergeos-bounties/NeraJob/issues/22) |

---

## Stack

- **Python** 3.11+
- **CLI:** Typer + Rich
- **HTTP:** httpx
- **HTML (when needed):** BeautifulSoup4 + lxml
- **Models:** Pydantic v2
- **Storage:** local JSON under `data/`

---

## Quick start

```bash
cd NeraJob
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -e ".[dev]"
nerajob --help
nerajob version
```

---

## Common commands

```bash
# Initialize a local profile (CV seed)
nerajob profile init

# Edit data/profile.json, then validate
nerajob profile show

# Scan (sample offline, remoteok live, or ATS boards)
nerajob scan --source sample -q "python backend" -l remote -n 20
nerajob scan --source remoteok -q "python" -n 20
nerajob scan --source lever -q engineer -n 10
nerajob scan --source ashby -q python -n 10
nerajob scan --all -q python -n 15

# Build a CV (Markdown + plain text)
nerajob cv build --target "Backend Engineer"

# Prepare an apply package for one job id
nerajob apply prepare --job-id <id>

# List saved jobs
nerajob jobs list
```

---

## Architecture

```
src/nerajob/
  cli.py              # Typer CLI entry
  config.py           # paths + HTTP settings
  models.py           # Job, Profile, Application models
  storage.py          # JSON persistence under data/
  scrapers/
    base.py           # BaseScraper protocol
    registry.py       # built-in scrapers (keep SOURCES.md in sync)
    sample.py         # offline sample feed
    remoteok.py       # RemoteOK public API adapter
    lever.py          # Lever public postings (per-company board)
    ashby.py          # Ashby public job board (per-company board)
  cv/
    builder.py        # CV generation from profile + target role
  apply/
    assistant.py      # cover note + checklist + package export
```

---

## Data layout

```
data/
  profile.json        # your profile / CV source of truth
  jobs.json           # scanned jobs cache
  applications/       # per-job apply packages
```

`data/` is gitignored except for example fixtures. Do not commit real CVs, API keys, or credentials.

---

## Adding a job site

1. Create `src/nerajob/scrapers/mysite.py` implementing `BaseScraper.search(query, location, limit)`
2. Register it in `scrapers/registry.py`
3. Add tests under `tests/` with **mocked HTTP** (CI must not depend on live network)
4. Update **[docs/SOURCES.md](docs/SOURCES.md)** and the tables in this README
5. Prefer official APIs; document rate limits and ToS notes in the PR

See [docs/BOUNTY.md](docs/BOUNTY.md) for MergeOS scraper bounty acceptance.

---

## Compliance

NeraJob is built for **ethical, ToS-aware** job discovery:

- Prefer **official / public APIs** over brittle HTML scrapers  
- Respect **robots.txt**, published rate limits, and site **Terms of Service**  
- **Never** commit secrets, long-lived tokens, or production `.env` values  
- Degrade gracefully on network failure (`[]` + optional sample fallback)  
- CI uses mocks — live smoke is optional and manual  

Details: [docs/SOURCES.md § Compliance](docs/SOURCES.md#compliance).

---

## Development

```bash
pytest -q
ruff check src tests
```

Optional live smoke (network required):

```bash
nerajob scan --source remoteok -q python -n 5
```

---

## MergeOS bounties (claim MRG)

NeraJob issues labeled `bounty` pay **MRG** via MergeOS after merge.

1. Read [docs/BOUNTY.md](docs/BOUNTY.md)
2. Pick an open issue with `reward:*-mrg` (high demand: **scrapers** — see tables above)
3. Star this repo + [mergeos](https://github.com/mergeos-bounties/mergeos); claim on the issue and [Claim Token #1](https://github.com/mergeos-bounties/mergeos/issues/1)
4. Open a PR to this repo (`Fixes #N`)
5. Maintainer merges and credits `github:<you>` on the MergeOS ledger (25 / 50 / 100 / 200 scale)

Docs bounty for this catalog: [#23](https://github.com/mergeos-bounties/NeraJob/issues/23).

---

## MergeOS

NeraJob is a sister project under [mergeos-bounties](https://github.com/mergeos-bounties). Parent OS: [mergeos-bounties/mergeos](https://github.com/mergeos-bounties/mergeos).

Roadmap: [docs/ROADMAP.md](docs/ROADMAP.md) · Sources: [docs/SOURCES.md](docs/SOURCES.md)

---

## License

MIT
