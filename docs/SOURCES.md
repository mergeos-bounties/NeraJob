# NeraJob — job sources catalog

Canonical list of **implemented** and **planned** job boards / ATS feeds for NeraJob scrapers.

> **Keep in sync with** `src/nerajob/scrapers/registry.py`.  
> Prefer **official / public APIs**. Always respect Terms of Service, robots.txt, rate limits, and privacy law.

---

## Status legend

| Status | Meaning |
| --- | --- |
| **Shipped** | Registered in `registry.py`, usable via `nerajob scan --source <name>` |
| **Planned** | Open bounty / roadmap item — not registered yet |
| **API key** | Requires env var or free developer key (never commit secrets) |
| **Public JSON** | No key for basic public feed (still subject to ToS) |

---

## Implemented sources (shipped)

| CLI `--source` | Site | Region / focus | Access | Module | Notes |
| --- | --- | --- | --- | --- | --- |
|| `sample` | Offline demo feed | Global (fixture) | None (offline) | `scrapers/sample.py` | Deterministic roles for demos, tests, CI. **No network.** |
|| `remoteok` | [RemoteOK](https://remoteok.com) | Remote / worldwide | Public JSON `https://remoteok.com/api` | `scrapers/remoteok.py` | Thin live adapter. Filters client-side by query tags/title. On network failure returns `[]` (CLI may fall back to `sample`). |
|| `remotive` | [Remotive](https://remotive.com) | Remote / worldwide | Public API `https://remotive.com/api/remote-jobs` | `scrapers/remotive.py` | Live public API. Set `NERAJOB_REMOTIVE_OFFLINE=1` for offline samples. |
|| `arbeitnow` | [Arbeitnow](https://www.arbeitnow.com) | Remote / EU-focused | Public API `https://www.arbeitnow.com/api/job-board/feeds` | `scrapers/arbeitnow.py` | Live public API. Set `NERAJOB_ARBEITNOW_OFFLINE=1` for offline samples. |
|| `jobicy` | [Jobicy](https://jobicy.com) | Remote / worldwide | Public JSON `https://jobicy.com/api/v2/remote-jobs` | `scrapers/jobicy.py` | Live public API. Set `NERAJOB_JOBICY_OFFLINE=1` for offline samples. |
|| `himalayas` | [Himalayas](https://himalayas.app) | Remote / worldwide | Public JSON `https://himalayas.app/jobs/api` | `scrapers/himalayas.py` | Free public API, no key required. Set `NERAJOB_HIMALAYAS_OFFLINE=1` for offline samples. |
|| `themuse` | [The Muse](https://www.themuse.com) | Company + job content | Public API `https://www.themuse.com/api/public/jobs` | `scrapers/themuse.py` | Rate-limited public API. Set `NERAJOB_THEMUSE_OFFLINE=1` for offline samples. |
|| `findwork` | [Findwork.dev](https://findwork.dev) | Developer jobs | API `https://findwork.dev/api/jobs/` | `scrapers/findwork.py` | Set `NERAJOB_FINDWORK_KEY` for live. No env → offline samples. |
|| `adzuna` | [Adzuna](https://developer.adzuna.com) | Multi-country search | API `https://api.adzuna.com/v1/api/jobs` | `scrapers/adzuna.py` | Requires `ADZUNA_APP_ID` and `ADZUNA_APP_KEY`. Without env → offline samples. |
|| `github_jobs` | [GitHub Jobs](https://jobs.github.com) | Developer jobs (legacy) | Public JSON `https://jobs.github.com/positions.json` | `scrapers/github_jobs.py` | API deprecated but demonstrates pattern. Set `NERAJOB_GITHUB_OFFLINE=1` for offline samples. |
|| `lever` | [Lever](https://www.lever.co) | Per-company career board | Public JSON `https://api.lever.co/v0/postings/<board>?mode=json` | `scrapers/lever.py` | Set `NERAJOB_LEVER_BOARD` for live. No env → offline sample posting (tests/demos). |
|| `ashby` | [Ashby](https://www.ashbyhq.com) | Per-company career board | Public JSON `https://api.ashbyhq.com/posting-api/job-board/<board_id>` | `scrapers/ashby.py` | Set `NERAJOB_ASHBY_BOARD` for live. No env → offline sample posting (tests/demos). |
|| `greenhouse` | [Greenhouse](https://developers.greenhouse.io/job-board.html) | Per-company career board | Public JSON `https://boards-api.greenhouse.io/v1/boards/{board}/jobs` | `scrapers/greenhouse.py` | Set `NERAJOB_GREENHOUSE_BOARD` for live. No env → offline samples. |
|| `smartrecruiters` | [SmartRecruiters](https://developers.smartrecruiters.com) | Company-scoped boards | Public JSON `https://api.smartrecruiters.com/v1/companies/{id}/postings` | `scrapers/smartrecruiters.py` | Set `NERAJOB_SMARTRECRUITERS_COMPANIES` (comma-separated IDs). |
|| `weworkremotely` | [We Work Remotely](https://weworkremotely.com) | Remote / worldwide | RSS `https://weworkremotely.com/categories/remote-programming-jobs.rss` | `scrapers/weworkremotely.py` | RSS feed adapter. Set `NERAJOB_WWR_OFFLINE=1` for offline samples. |

### CLI examples

```bash
# Offline demo
nerajob scan --source sample -q python -n 10

# Live RemoteOK
nerajob scan --source remoteok -q "python backend" -n 20

# Lever / Ashby company boards
# export NERAJOB_LEVER_BOARD=netflix   # Windows: set NERAJOB_LEVER_BOARD=netflix
nerajob scan --source lever -q engineer -n 20
# export NERAJOB_ASHBY_BOARD=openai
nerajob scan --source ashby -q python -n 20

# All registered scrapers
nerajob scan --all -q python -l remote -n 15
```

### Implementation checklist (when adding a source)

1. `src/nerajob/scrapers/<name>.py` implementing `BaseScraper.search(query, location, limit)`
2. Register in `scrapers/registry.py`
3. Tests with **mocked HTTP** (CI must not hit live network)
4. Document row in **this file** + README “Supported job sources”
5. Graceful degrade on network/API errors (`return []`, no crash)

---

## Planned sources (bounty backlog)

Linked to open issues on [mergeos-bounties/NeraJob](https://github.com/mergeos-bounties/NeraJob). Claim via MergeOS MRG — see [BOUNTY.md](BOUNTY.md).

### Remote / global public feeds

| Planned `--source` | Site | Access (typical) | Bounty issue | Priority notes |
| --- | --- | --- | --- | --- |
| _(all shipped — see implemented table above)_ | | | |

### Aggregators & national / multi-country APIs

| Planned `--source` | Site | Access (typical) | Bounty issue | Priority notes |
| --- | --- | --- | --- | --- |
| `usajobs` | [USAJOBS](https://developer.usajobs.gov) | Official API + User-Agent / auth headers | [#8](https://github.com/mergeos-bounties/NeraJob/issues/8) | US federal listings |
| `reed` | [Reed.co.uk](https://www.reed.co.uk/developers) | API key | [#9](https://github.com/mergeos-bounties/NeraJob/issues/9) | UK jobs |
| `jooble` | [Jooble](https://jooble.org/api/about) | API key | [#15](https://github.com/mergeos-bounties/NeraJob/issues/15) | Multi-region aggregator |
| `arbeitnow-eu` / pack | Arbeitnow + EU/EURES-oriented | Public / documented feeds | [#16](https://github.com/mergeos-bounties/NeraJob/issues/16) | EU remote pack |

### Company career boards (ATS public JSON)

| Planned `--source` | Site / ATS | Access (typical) | Bounty issue | Priority notes |
| --- | --- | --- | --- | --- |
| _(all shipped — see implemented table above)_ | | | |

> **Shipped:** `remoteok` (#19), `remotive` (#2), `arbeitnow` (#3), `jobicy` (#4), `himalayas` (#5), `findwork` (#6), `adzuna` (#7), `themuse` (#10), `greenhouse` (#11), `smartrecruiters` (#14), `lever` (#12 / #25), `ashby` (#13 / #24), `weworkremotely`, `github_jobs` — see implemented table above.

### Vietnam / regional (ToS-safe only)

| Planned `--source` | Site | Access (typical) | Bounty issue | Priority notes |
| --- | --- | --- | --- | --- |
| `topcv` / `vietnamworks` | TopCV or VietnamWorks | **Only** ToS-safe public pages or official partner APIs | [#17](https://github.com/mergeos-bounties/NeraJob/issues/17) | Prefer official APIs; no aggressive HTML scraping that violates ToS |

### Platform / multi-scraper work

| Work item | Description | Bounty issue |
| --- | --- | --- |
| Shared HTTP framework | Retries, rate limit, robots-aware policy | [#18](https://github.com/mergeos-bounties/NeraJob/issues/18) |
| `scan --all` + dedupe | Aggregate multi-source, dedupe by URL / title+company | [#19](https://github.com/mergeos-bounties/NeraJob/issues/19) |
| Multi-source pack | Ship 5+ live public scrapers with CI mocks | [#22](https://github.com/mergeos-bounties/NeraJob/issues/22) |

---

## Auth / environment variables (planned keys)

Document expected env names so adapters stay consistent. **Never commit real keys.**

| Variable | Used by | Required |
| --- | --- | --- |
| *(none)* | `sample`, `remoteok`, `himalayas`, `themuse`, `weworkremotely` | — |
| `NERAJOB_LEVER_BOARD` | `lever` | Optional; without it uses offline sample postings |
| `NERAJOB_ASHBY_BOARD` | `ashby` | Optional; without it uses offline sample postings |
| `NERAJOB_GREENHOUSE_BOARD` | `greenhouse` | Optional; without it uses offline sample postings |
| `NERAJOB_SMARTRECRUITERS_COMPANIES` | `smartrecruiters` | Optional; comma-separated company IDs |
| `NERAJOB_FINDWORK_KEY` | `findwork` | Optional; without it uses offline sample postings |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` | `adzuna` | Required for live search |
| `NERAJOB_GITHUB_OFFLINE` | `github_jobs` | Optional; `1` to force offline samples |
| `NERAJOB_REMOTIVE_OFFLINE` | `remotive` | Optional; `1` to force offline samples |
| `NERAJOB_ARBEITNOW_OFFLINE` | `arbeitnow` | Optional; `1` to force offline samples |
| `NERAJOB_JOBICY_OFFLINE` | `jobicy` | Optional; `1` to force offline samples |
| `NERAJOB_HIMALAYAS_OFFLINE` | `himalayas` | Optional; `1` to force offline samples |
| `NERAJOB_WWR_OFFLINE` | `weworkremotely` | Optional; `1` to force offline samples |
| `NERAJOB_THEMUSE_OFFLINE` | `themuse` | Optional; `1` to force offline samples |
| `REED_API_KEY` | `reed` (planned) | Yes |
| `JOOBLE_API_KEY` | `jooble` (planned) | Yes |
| `USAJOBS_API_KEY` / `USAJOBS_USER_AGENT` | `usajobs` (planned) | Per USAJOBS developer docs |
| `NERAJOB_HTTP_TIMEOUT` | all HTTP scrapers | Optional (seconds) |
| `NERAJOB_USER_AGENT` | all HTTP scrapers | Optional polite UA string |

When an adapter needs a missing key: log a clear CLI message and return `[]` (do not crash).

---

## Compliance

1. Prefer **official public APIs** and **user-owned** data over scraping HTML.
2. Respect **robots.txt**, published rate limits, and site **Terms of Service**.
3. Do not store or commit API secrets, session cookies, or personal applicant data beyond local `data/` (gitignored).
4. For regional boards (Vietnam, etc.): only ToS-safe approaches; reject PRs that hardcode blocked scrapers or captcha bypass.
5. CI tests must use **mocked** HTTP — live network optional for manual smoke only.

---

## Tiếng Việt (tóm tắt)

| Trạng thái | Nguồn | Ghi chú |
| --- | --- | --- |
| Đã có | `sample` | Demo offline, không cần mạng |
| Đã có | `remoteok` | API JSON public RemoteOK |
| Đã có | `remotive` | API JSON public Remotive |
| Đã có | `arbeitnow` | API JSON public Arbeitnow |
| Đã có | `jobicy` | API JSON public Jobicy |
| Đã có | `himalayas` | API JSON public Himalayas |
| Đã có | `themuse` | API JSON public The Muse |
| Đã có | `findwork` | API Findwork (cần key) |
| Đã có | `adzuna` | API Adzuna (cần key) |
| Đã có | `github_jobs` | API JSON GitHub Jobs (legacy) |
| Đã có | `lever` | Board công ty Lever; env `NERAJOB_LEVER_BOARD` |
| Đã có | `ashby` | Board công ty Ashby; env `NERAJOB_ASHBY_BOARD` |
| Đã có | `greenhouse` | Board công ty Greenhouse; env `NERAJOB_GREENHOUSE_BOARD` |
| Đã có | `smartrecruiters` | Board công ty SmartRecruiters |
| Đã có | `weworkremotely` | RSS We Work Remotely |
| Sắp tới | USAJOBS, Reed, Jooble, board VN (TopCV/VNW ToS-safe) | Xem issue bounty tương ứng |

Luôn tôn trọng điều khoản site, rate limit, và không commit secret.

---

*Catalog maintained in sync with `src/nerajob/scrapers/registry.py`. Issue #23 (MRG bounty) — see [BOUNTY.md](BOUNTY.md).*



## Related docs

- [README.md](../README.md) — product overview + quick start  
- [BOUNTY.md](BOUNTY.md) — claim MRG for scrapers  
- [ROADMAP.md](ROADMAP.md) — product milestones  

<!-- bounty #23 catalog evidence: docs/sources-evidence.png -->
