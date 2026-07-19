# Ethical Scraping & Rate Limit Policy

NeraJob scrapes public job boards to help job seekers find opportunities. This document outlines our ethical scraping principles and rate limit policy for contributors adding or maintaining scrapers.

## Principles

1. **Respect robots.txt** — Always check and obey `robots.txt` before scraping any site. Never scrape paths marked `Disallow`.
2. **Identify yourself** — Set a descriptive `User-Agent` header that identifies the scraper as `NeraJob/{version}` with a contact method.
3. **Rate limit** — Add delays between requests. Default minimum: **1 second** between requests to the same host.
4. **Cache responses** — Store results locally and reuse them. Avoid re-scraping the same endpoint within 24 hours.
5. **No authentication bypass** — Only scrape publicly accessible pages. Never use stolen credentials, reverse-engineered private APIs, or bypass paywalls.
6. **No personal data collection** — Scrape only job posting data (title, company, location, description). Never collect applicant or user data.
7. **Handle errors gracefully** — On HTTP 429 (rate limit), 503 (service unavailable), or connection errors, back off with exponential delay (1s, 2s, 4s, 8s, max 60s) and log the failure.
8. **Offline fallback** — Every scraper must work with `NERAJOB_*_OFFLINE=1` (or equivalent) for testing without hitting live servers. Provide sample fixture data for offline mode.
9. **Respect server load** — Keep concurrent connections to a single host at 1 (no parallelism per host). Use a shared HTTP client with connection pooling limits.
10. **Comply with laws** — Follow applicable laws including GDPR (EU), CCPA (California), and the Computer Fraud and Abuse Act (US). If a site's terms of service prohibit scraping, do not scrape it.

## Rate limit configuration

Each scraper should support these environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `NERAJOB_RATE_LIMIT_DELAY` | `1.0` | Seconds between requests to the same host |
| `NERAJOB_MAX_RETRIES` | `3` | Max retries on transient errors |
| `NERAJOB_REQUEST_TIMEOUT` | `15` | HTTP request timeout in seconds |
| `NERAJOB_OFFLINE` | `0` | Set to `1` to use offline fixture data for all scrapers |

Scraper-specific offline flags (`NERAJOB_{NAME}_OFFLINE=1`) override the global setting for individual scrapers.

## Backoff strategy

```
429 / 503 / connection error
  → wait 1s, retry
  → wait 2s, retry
  → wait 4s, retry
  → wait 8s, retry
  → wait 60s, retry
  → give up (log error, return offline fallback)
```

## User-Agent format

```
NeraJob/{version} (+https://github.com/mergeos-bounties/NeraJob)
```

Example: `NeraJob/0.1.0 (+https://github.com/mergeos-bounties/NeraJob)`

## Testing offline

All scrapers must provide an offline mode that returns sample data without making HTTP requests:

```bash
NERAJOB_ARBEITNOW_OFFLINE=1 nerajob scan --source arbeitnow -q python
NERAJOB_OFFLINE=1 nerajob scan --all -q engineer
```

## Adding a new scraper

1. Create a new file in `src/nerajob/scrapers/` following the `BaseScraper` interface
2. Implement `search()` with both live and offline paths
3. Add offline test fixtures inline
4. Register in `registry.py`
5. Add tests in `tests/` with offline mode
6. Verify: `NERAJOB_{NAME}_OFFLINE=1 pytest tests/test_{name}.py`

## License

This policy is part of the NeraJob project (MIT License). All scrapers in the codebase must comply with this policy.
