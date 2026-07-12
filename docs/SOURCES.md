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
|| `lever` | [Lever](https://www.lever.co) | Per-company career board | Public JSON `https://api.lever.co/v0/postings/<board>?mode=json` | `scrapers/lever.py` | Set `NERAJOB_LEVER_BOARD` for live. No env → offline sample posting (tests/demos). |
|| `ashby` | [Ashby](https://www.ashbyhq.com) | Per-company career board | Public JSON `https://api.ashbyhq.com/posting-api/job-board/<board_id>` | `scrapers/ashby.py` | Set `NERAJOB_ASHBY_BOARD` for live. No env → offline sample posting (tests/demos). |

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
|| `jobicy` | [Jobicy](https://jobicy.com) | Remote jobs API | [#4](https://github.com/mergeos-bounties/NeraJob/issues/4) | Remote focus |
| `himalayas` | [Himalayas](https://himalayas.app) | Public remote jobs API | [#5](https://github.com/mergeos-bounties/NeraJob/issues/5) | Remote + salary metadata |
| `findwork` | [Findwork.dev](https://findwork.dev) | API + optional key | [#6](https://github.com/mergeos-bounties/NeraJob/issues/6) | Dev jobs |

### Aggregators & national / multi-country APIs

| Planned `--source` | Site | Access (typical) | Bounty issue | Priority notes |
| --- | --- | --- | --- | --- |
| `adzuna` | [Adzuna](https://developer.adzuna.com) | API key (`ADZUNA_APP_ID`, `ADZUNA_APP_KEY`) | [#7](https://github.com/mergeos-bounties/NeraJob/issues/7) | Multi-country search |
| `usajobs` | [USAJOBS](https://developer.usajobs.gov) | Official API + User-Agent / auth headers | [#8](https://github.com/mergeos-bounties/NeraJob/issues/8) | US federal listings |
| `reed` | [Reed.co.uk](https://www.reed.co.uk/developers) | API key | [#9](https://github.com/mergeos-bounties/NeraJob/issues/9) | UK jobs |
| `themuse` | [The Muse](https://www.themuse.com/developers/api/v2) | Public API (rate-limited) | [#10](https://github.com/mergeos-bounties/NeraJob/issues/10) | Company + job content |
| `jooble` | [Jooble](https://jooble.org/api/about) | API key | [#15](https://github.com/mergeos-bounties/NeraJob/issues/15) | Multi-region aggregator |
| `arbeitnow-eu` / pack | Arbeitnow + EU/EURES-oriented | Public / documented feeds | [#16](https://github.com/mergeos-bounties/NeraJob/issues/16) | EU remote pack |

### Company career boards (ATS public JSON)

| Planned `--source` | Site / ATS | Access (typical) | Bounty issue | Priority notes |
| --- | --- | --- | --- | --- |
| `greenhouse` | [Greenhouse](https://developers.greenhouse.io/job-board.html) | Public board JSON (`boards.greenhouse.io`) | [#11](https://github.com/mergeos-bounties/NeraJob/issues/11) | Per-company board token list |
| `smartrecruiters` | [SmartRecruiters](https://developers.smartrecruiters.com) | Public postings | [#14](https://github.com/mergeos-bounties/NeraJob/issues/14) | Company-scoped boards |

> **Shipped:** `remoteok` (#19), `remotive` (#2), `arbeitnow` (#3), `lever` (#12 / #25), `ashby` (#13 / #24) — see implemented table above.

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
| *(none)* | `sample`, `remoteok` | — |
| `NERAJOB_LEVER_BOARD` | `lever` | Optional; without it uses offline sample postings |
| `NERAJOB_ASHBY_BOARD` | `ashby` | Optional; without it uses offline sample postings |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` | `adzuna` (planned) | Yes for live search |
| `REED_API_KEY` | `reed` (planned) | Yes |
| `JOOBLE_API_KEY` | `jooble` (planned) | Yes |
| `USAJOBS_API_KEY` / `USAJOBS_USER_AGENT` | `usajobs` (planned) | Per USAJOBS developer docs |
| `FINDWORK_API_KEY` | `findwork` (planned) | Optional / tier-dependent |
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
| Đã có | `lever` | Board công ty Lever; env `NERAJOB_LEVER_BOARD` |
| Đã có | `ashby` | Board công ty Ashby; env `NERAJOB_ASHBY_BOARD` |
| Sắp tới | Remotive, Arbeitnow, Jobicy, Himalayas, Findwork, Adzuna, USAJOBS, Reed, The Muse, Greenhouse, SmartRecruiters, Jooble, board VN (TopCV/VNW ToS-safe) | Xem issue bounty tương ứng |

Luôn tôn trọng điều khoản site, rate limit, và không commit secret.

---

*Catalog maintained in sync with `src/nerajob/scrapers/registry.py`. Issue #23 (MRG bounty) — see [BOUNTY.md](BOUNTY.md).*



## Related docs

- [README.md](../README.md) — product overview + quick start  
- [BOUNTY.md](BOUNTY.md) — claim MRG for scrapers  
- [ROADMAP.md](ROADMAP.md) — product milestones  

<!-- bounty #23 catalog evidence: docs/sources-evidence.png -->
