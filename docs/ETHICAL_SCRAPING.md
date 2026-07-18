# Ethical Scraping & Rate Limit Policy

NeraJob scrapes public job boards to help job seekers find opportunities. This document outlines our ethical scraping principles, rate limit policy, and source-specific Terms of Service (ToS) notes for contributors adding or maintaining scrapers.

**Issue:** Fixes #53 — Documents robots/ToS, rate limits, and preferred official APIs for new scrapers.

---

## Table of Contents

1. [Principles](#principles)
2. [Preferred Official APIs](#preferred-official-apis)
3. [Source-Specific ToS & robots.txt Notes](#source-specific-tos--robotstxt-notes)
4. [Rate Limit Configuration](#rate-limit-configuration)
5. [Exponential Backoff Strategy](#exponential-backoff-strategy)
6. [User-Agent Standard](#user-agent-standard)
7. [Testing Offline](#testing-offline)
8. [Adding a New Scraper](#adding-a-new-scraper)
9. [Compliance Checklist](#compliance-checklist)
10. [License](#license)

---

## Principles

1. **Prefer official APIs over HTML scraping** — Always check if a source publishes an official REST/GraphQL/RSS API before scraping HTML. APIs are more stable, faster, and explicitly licensed for programmatic access.
2. **Respect robots.txt** — Always check and obey `robots.txt` before scraping any site. Never scrape paths marked `Disallow`. Verify at `https://{host}/robots.txt`.
3. **Identify yourself** — Set a descriptive `User-Agent` header that identifies the scraper as `NeraJob/{version}` with a contact method (project URL).
4. **Rate limit** — Add delays between requests. Default minimum: **1 second** between requests to the same host. Stricter limits apply per-source (see [Source-Specific Notes](#source-specific-tos--robotstxt-notes)).
5. **Cache responses** — Store results locally and reuse them. Avoid re-scraping the same endpoint within 24 hours. Use the `data/jobs.json` cache file.
6. **No authentication bypass** — Only scrape publicly accessible pages. Never use stolen credentials, reverse-engineered private APIs, or bypass paywalls.
7. **No personal data collection** — Scrape only job posting data (title, company, location, description, tags). Never collect applicant names, emails, phone numbers, or other PII.
8. **Handle errors gracefully** — On HTTP 429 (rate limit), 503 (service unavailable), or connection errors, back off with exponential delay (1s, 2s, 4s, 8s, max 60s) and log the failure. Fall back to offline fixtures when retries are exhausted.
9. **Offline fallback** — Every scraper must work with `NERAJOB_*_OFFLINE=1` (or equivalent) for testing without hitting live servers. Provide sample fixture data for offline mode.
10. **Respect server load** — Keep concurrent connections to a single host at 1 (no parallelism per host). Use the shared HTTP client with connection pooling limits.
11. **Comply with laws** — Follow applicable laws including GDPR (EU), CCPA (California), and the Computer Fraud and Abuse Act (US). If a site's terms of service prohibit scraping, do not scrape it.
12. **Honor `Retry-After` header** — When a 429 or 503 response includes a `Retry-After` header, wait the specified duration before retrying (overrides the default backoff).

---

## Preferred Official APIs

When adding a new scraper, **always check for an official API first**. The table below lists sources supported by NeraJob and their preferred programmatic access method.

| Source | Type | Endpoint | Auth | Rate Limit | ToS Reference |
|---|---|---|---|---|---|
| **Arbeitnow** | REST JSON | `https://www.arbeitnow.com/api/job-board-api` | None (public) | 60 req/min | [arbeitnow.com/api](https://www.arbeitnow.com/api/job-board-api) |
| **Remotive** | REST JSON | `https://remotive.com/api/remote-jobs` | None (public) | 100 req/hour | [remotive.com/api](https://remotive.com/api-documentation) |
| **RemoteOK** | REST JSON | `https://remoteok.com/api` | None (public) | 60 req/min | [remoteok.com/api](https://remoteok.com/api) |
| **Jobicy** | REST JSON | `https://jobicy.com/api/v2/remote-jobs` | None (public) | 60 req/min | [jobicy.com/api](https://jobicy.com/api) |
| **WeWorkRemotely** | RSS 2.0 | `https://weworkremotely.com/remote-jobs.rss` | None (public) | 30 req/min | [weworkremotely.com](https://weworkremotely.com/) |
| **The Muse** | REST JSON | `https://www.themuse.com/api/public/jobs` | API key (free) | 3600 req/hour | [themuse.com/developers/api](https://www.themuse.com/developers/api/public) |
| **Lever** | REST JSON | `https://api.lever.co/v0/postings/{board}` | None (public boards) | 1000 req/hour | [lever.co/postings_api](https://github.com/lever/postings-api/blob/master/README.md) |
| **Ashby** | REST JSON | `https://api.ashbyhq.com/posting-api/job-board/{board}` | None (public boards) | 100 req/min | [ashbyhq.com/api](https://developers.ashbyhq.com/) |
| **SmartRecruiters** | REST JSON | `https://api.smartrecruiters.com/v1/companies/{id}/postings` | None (public) | 100 req/min | [smartrecruiters.com/api](https://dev.smartrecruiters.com/) |
| **Findwork.dev** | REST JSON | `https://findwork.dev/api/jobs/` | Token (free) | 60 req/min | [findwork.dev/api](https://findwork.dev/api/) |
| **Himalayas.app** | REST JSON | `https://himalayas.app/api/jobs` | None (public) | 60 req/min | [himalayas.app/api](https://himalayas.app/api) |
| **USAJOBS** | REST JSON | `https://data.usajobs.gov/api/search` | API key (free) | 1000 req/hour | [developer.usajobs.gov](https://developer.usajobs.gov/) |
| **Adzuna** *(planned)* | REST JSON | `https://developer.adzuna.com/api/v1/api/jobs/` | API key (free) | 250 req/day | [developer.adzuna.com](https://developer.adzuna.com/docs) |
| **Reed.co.uk** *(planned)* | REST JSON | `https://www.reed.co.uk/api/1.0/search` | API key (free) | 100 req/min | [reed.co.uk/developers](https://www.reed.co.uk/developers/jobseeker/overview) |
| **Jooble** *(planned)* | REST XML | `https://jooble.org/api/` | API key (free) | 500 req/day | [jooble.org/api](https://jooble.org/api/about) |

### Source Selection Priority

When a new job source is proposed, apply the following priority order:

1. **Tier A — Official public API, no auth required** (e.g., Arbeitnow, Remotive, Himalayas): preferred — no user friction, well-documented, low ToS risk.
2. **Tier B — Official API with free API key** (e.g., The Muse, Findwork.dev, USAJOBS, Adzuna): acceptable — key registration is automated and free.
3. **Tier C — RSS/Atom feed** (e.g., WeWorkRemotely): acceptable — feeds are designed for programmatic consumption.
4. **Tier D — Public HTML scraping**: discouraged — only when no API exists. Must respect robots.txt, rate limit aggressively (≥3s between requests), and provide offline fixtures.
5. **Tier E — Authenticated/private API**: forbidden — never scrape behind login walls, paid subscriptions, or proprietary APIs requiring NDA.

---

## Source-Specific ToS & robots.txt Notes

### Arbeitnow
- **ToS:** Public API explicitly provided for programmatic access. No registration required.
- **robots.txt:** `https://www.arbeitnow.com/robots.txt` — allows `/api/*`.
- **Notes:** Returns JSON with `data` array. Supports `?page=N` pagination.

### Remotive
- **ToS:** Public API explicitly documented at [remotive.com/api-documentation](https://remotive.com/api-documentation). Free for non-commercial use.
- **robots.txt:** API path not restricted.
- **Notes:** Returns all jobs in a single response — no pagination required. Use client-side filtering.

### RemoteOK
- **ToS:** Public API at [remoteok.com/api](https://remoteok.com/api). Free for non-commercial use with attribution.
- **robots.txt:** `/api/*` allowed.
- **Notes:** Response includes a metadata object at index 0 — skip it when iterating results.

### Jobicy
- **ToS:** Public API documented at [jobicy.com/api](https://jobicy.com/api). Free.
- **robots.txt:** API path not restricted.
- **Notes:** Supports `?tag=python&category=software` filters.

### WeWorkRemotely
- **ToS:** RSS feed publicly available for personal/aggregator use. No official API. [weworkremotely.com](https://weworkremotely.com/) ToS permits linking to job URLs.
- **robots.txt:** `/remote-jobs.rss` allowed.
- **Notes:** RSS 2.0 format. Use `feedparser` or `lxml` to parse.

### The Muse
- **ToS:** Public API with free API key at [themuse.com/developers/api](https://www.themuse.com/developers/api/public). ToS requires attribution.
- **robots.txt:** API path not restricted.
- **Notes:** Pagination via `?page=N`. Max 100 results per page. 3600 req/hour per IP.

### Lever
- **ToS:** Public postings API at [lever.co/postings-api](https://github.com/lever/postings-api). Free for public boards.
- **robots.txt:** API path not restricted.
- **Notes:** Requires `board_name` (company slug). Returns all postings for that board.

### Ashby
- **ToS:** Posting API at [developers.ashbyhq.com](https://developers.ashbyhq.com/). Public boards accessible without auth.
- **robots.txt:** API path not restricted.
- **Notes:** Requires `board_id`. Returns structured job postings with location details.

### SmartRecruiters
- **ToS:** Public API at [dev.smartrecruiters.com](https://dev.smartrecruiters.com/). Free for public postings.
- **robots.txt:** API path not restricted.
- **Notes:** Requires `company_id`. Supports `?limit=N&offset=N` pagination.

### Findwork.dev
- **ToS:** Public API with free token at [findwork.dev/api](https://findwork.dev/api/). ToS requires token in `Authorization: Token {token}` header.
- **robots.txt:** API path not restricted.
- **Notes:** Pagination via `?page=N` (cursor-based). 60 req/min per token.

### Himalayas.app
- **ToS:** Public API at [himalayas.app/api](https://himalayas.app/api). Free for non-commercial use.
- **robots.txt:** API path not restricted.
- **Notes:** Returns JSON with `jobs` array. Supports `?search=python&location=remote` filters.

### USAJOBS
- **ToS:** Public API at [developer.usajobs.gov](https://developer.usajobs.gov/). Free API key required (register at https://developer.usajobs.gov/APIRequest/Index).
- **robots.txt:** API path not restricted.
- **Notes:** Requires `Authorization-Key` header (not standard `Authorization`). Supports `?Keyword=python&LocationName=Washington` filters. 1000 req/hour per key.

### Sources NOT to scrape

The following sources are explicitly excluded from NeraJob due to ToS restrictions or authentication barriers:

- **LinkedIn** — ToS prohibits scraping; requires login for full data. Use [official LinkedIn Jobs API](https://docs.microsoft.com/en-us/linkedin/shared/api-guide/concepts/jobs) (requires partnership approval).
- **Indeed** — ToS prohibits scraping; provides [publisher API](https://developers.indeed.com/) but requires application review.
- **Glassdoor** — ToS prohibits scraping; API access requires employer account.
- **Monster** — ToS prohibits automated access; no public API.
- **StepStone** — ToS prohibits scraping; no public API.

---

## Rate Limit Configuration

Each scraper should support these environment variables:

| Variable | Default | Description |
|---|---|---|
| `NERAJOB_RATE_LIMIT_DELAY` | `1.0` | Seconds between requests to the same host |
| `NERAJOB_MAX_RETRIES` | `3` | Max retries on transient errors (429, 503, network) |
| `NERAJOB_REQUEST_TIMEOUT` | `20` | HTTP request timeout in seconds |
| `NERAJOB_OFFLINE` | `0` | Set to `1` to use offline fixture data for all scrapers |
| `NERAJOB_USER_AGENT` | `NeraJob/{version} (+https://github.com/mergeos-bounties/NeraJob)` | Custom User-Agent header |
| `NERAJOB_HTTP_TIMEOUT` | `20` | Alias for `NERAJOB_REQUEST_TIMEOUT` |

Scraper-specific offline flags (`NERAJOB_{NAME}_OFFLINE=1`) override the global setting for individual scrapers. For example:

- `NERAJOB_ARBEITNOW_OFFLINE=1`
- `NERAJOB_REMOTIVE_OFFLINE=1`
- `NERAJOB_FINDWORK_OFFLINE=1`
- `NERAJOB_HIMALAYAS_OFFLINE=1`
- `NERAJOB_USAJOBS_OFFLINE=1`

Scraper-specific API tokens:

- `NERAJOB_FINDWORK_API_TOKEN` — Required for live Findwork.dev API
- `NERAJOB_USAJOBS_API_KEY` — Required for live USAJOBS API
- `NERAJOB_THE_MUSE_API_KEY` — Required for live The Muse API
- `NERAJOB_LEVER_BOARD` — Company slug for Lever
- `NERAJOB_ASHBY_BOARD` — Board ID for Ashby
- `NERAJOB_SMARTRECRUITERS_COMPANIES` — Comma-separated company IDs

---

## Exponential Backoff Strategy

When a request fails with HTTP 429, 503, or a connection error, apply the following exponential backoff:

```
Request fails (429 / 503 / connection error)
  ↓
  Check Retry-After header
  ├─ If present: sleep(Retry-After seconds) → retry
  └─ If absent: exponential backoff
     ├─ Attempt 1: wait 1s, retry
     ├─ Attempt 2: wait 2s, retry
     ├─ Attempt 3: wait 4s, retry
     ├─ Attempt 4: wait 8s, retry
     ├─ Attempt 5: wait 16s, retry
     ├─ Attempt 6: wait 32s, retry
     ├─ Attempt 7: wait 60s (cap), retry
     └─ Give up → log error, return offline fixtures
```

**Implementation pattern:**

```python
import time
import httpx

MAX_RETRIES = 7
INITIAL_DELAY = 1.0
MAX_DELAY = 60.0

def fetch_with_backoff(client: httpx.Client, url: str, **kwargs) -> dict | None:
    delay = INITIAL_DELAY
    for attempt in range(MAX_RETRIES):
        try:
            response = client.get(url, **kwargs)
            if response.status_code in (429, 503):
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    time.sleep(float(retry_after))
                else:
                    time.sleep(delay)
                    delay = min(delay * 2, MAX_DELAY)
                continue
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ConnectionError):
            time.sleep(delay)
            delay = min(delay * 2, MAX_DELAY)
    return None  # caller falls back to offline fixtures
```

---

## User-Agent Standard

All HTTP requests made by NeraJob scrapers must include a `User-Agent` header in the following format:

```
NeraJob/{version} (+https://github.com/mergeos-bounties/NeraJob)
```

**Examples:**

- `NeraJob/0.2.63 (+https://github.com/mergeos-bounties/NeraJob)`
- `NeraJob/0.1.0 (+https://github.com/mergeos-bounties/NeraJob)` (default if version unknown)

**Override:** Set the `NERAJOB_USER_AGENT` environment variable to use a custom User-Agent (useful for testing or including a contact email).

```bash
export NERAJOB_USER_AGENT="NeraJob/0.2.63 (MyOrg; contact: ops@myorg.com)"
```

**Why identify yourself?** Many job board operators block generic browser-spoofing User-Agents (e.g., `Mozilla/5.0`). Identifying as NeraJob with a project URL allows operators to contact us if our traffic causes issues, and demonstrates good-faith compliance with their ToS.

---

## Testing Offline

All scrapers must provide an offline mode that returns sample data without making HTTP requests. This enables:

- **Reproducible tests** in CI without network access
- **Faster iteration** during development
- **Graceful degradation** when live APIs are down

```bash
# Test a single scraper in offline mode
NERAJOB_ARBEITNOW_OFFLINE=1 pytest tests/test_arbeitnow.py -v
NERAJOB_FINDWORK_OFFLINE=1 pytest tests/test_findwork.py -v
NERAJOB_HIMALAYAS_OFFLINE=1 pytest tests/test_himalayas.py -v
NERAJOB_USAJOBS_OFFLINE=1 pytest tests/test_usajobs.py -v

# Test all scrapers in offline mode
NERAJOB_OFFLINE=1 pytest tests/ -v

# Run CLI in offline mode (demo)
NERAJOB_OFFLINE=1 nerajob scan --all -q engineer
```

Offline fixtures must:

1. Be deterministic (same query → same results across runs)
2. Include at least 3 sample jobs per scraper
3. Cover edge cases: empty query, query with no matches, location filter
4. Be embedded in the scraper file (not external JSON) to keep tests self-contained

---

## Adding a New Scraper

Follow this checklist when adding a new source:

1. **Check for official API** — Visit the source's developer documentation. If an API exists, prefer it over HTML scraping.
2. **Read the ToS** — Verify that programmatic access is permitted. If the ToS prohibits scraping or requires a paid license, do not proceed.
3. **Check robots.txt** — Visit `https://{host}/robots.txt`. Note any restricted paths.
4. **Create the scraper file** — `src/nerajob/scrapers/{name}.py` following the `BaseScraper` interface:
   ```python
   class MySourceScraper(BaseScraper):
       name = "mysource"
       API_URL = "https://..."
       def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
           # Try live API
           # Fall back to offline fixtures on error
           ...
   ```
5. **Implement offline mode** — Provide `_OFFLINE` fixture list with at least 3 sample jobs.
6. **Add environment variables** — Support `NERAJOB_{NAME}_OFFLINE=1` and `NERAJOB_{NAME}_API_TOKEN` (if auth required).
7. **Register in `registry.py`** — Add the scraper to the `scrapers` list in `available_scrapers()`.
8. **Write tests** — `tests/test_{name}.py` covering:
   - Registration in `available_scrapers()`
   - Offline mode returns jobs
   - Query + location filtering
   - Live API path (mocked httpx)
   - Graceful fallback on API failure
9. **Document ToS in this file** — Add an entry to the [Source-Specific Notes](#source-specific-tos--robotstxt-notes) table.
10. **Verify compliance** — Run through the [Compliance Checklist](#compliance-checklist) below.

---

## Compliance Checklist

Before submitting a PR that adds or modifies a scraper, verify:

- [ ] Source has an official API (or no API exists and HTML scraping is justified)
- [ ] Source's ToS permits programmatic access
- [ ] `robots.txt` has been checked and respected
- [ ] `User-Agent` header includes `NeraJob/{version}` and project URL
- [ ] Default rate limit is ≥1 second between requests to the same host
- [ ] Exponential backoff is implemented for 429/503/connection errors
- [ ] `Retry-After` header is honored when present
- [ ] Offline mode works with `NERAJOB_{NAME}_OFFLINE=1`
- [ ] At least 3 offline fixtures are provided
- [ ] No PII is collected (only job posting data: title, company, location, description, tags)
- [ ] No authentication bypass (no login walls, no stolen credentials)
- [ ] Scraper is registered in `registry.py`
- [ ] Tests cover offline mode + live API path (mocked) + error fallback
- [ ] ToS notes added to this document

---

## License

This policy is part of the NeraJob project (MIT License). All scrapers in the codebase must comply with this policy. Violations should be reported as GitHub issues and will be addressed promptly.

For questions about specific source ToS or to request adding a new source, please open a GitHub issue with the `scraper-request` label.
