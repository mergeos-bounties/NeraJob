# NeraJob bounties (MergeOS MRG)

NeraJob pays contributors in **MRG** through the MergeOS bounty program.

## Before you start

1. **Star** this repository: https://github.com/mergeos-bounties/NeraJob  
2. **Star** MergeOS: https://github.com/mergeos-bounties/mergeos  
3. **Claim** on the linked NeraJob issue (comment: `I claim this bounty`)  
4. **Also claim** on MergeOS [Claim Token issue #1](https://github.com/mergeos-bounties/mergeos/issues/1) with a link to the NeraJob issue  
5. Open a PR against **NeraJob** `master` that references the issue (`Fixes #N`)

## Payout scale (admin ledger)

| Scope | Typical MRG |
| --- | ---: |
| Small scraper / bug / tests | 25 |
| Medium scraper + tests | 50 |
| Large multi-source / system feature | 100 |
| Extra-large product work | 200 |

Issue titles may show a marketing reward; **final credit is 25 / 50 / 100 / 200** after maintainer review.

## Acceptance (scrapers)

- Implement `BaseScraper` under `src/nerajob/scrapers/`
- Register in `scrapers/registry.py`
- Prefer **official public APIs** over brittle HTML scraping
- Respect robots.txt, rate limits, and site Terms of Service
- Unit tests with mocked HTTP (no live network required in CI)
- `nerajob scan --source <name>` works
- Document source + env vars (if any) in PR body

## Evidence

- Backend/scraper: test output + sample `nerajob scan` command log  
- UI (if any): screenshots  

## After merge

Maintainer merges the PR on NeraJob and credits MRG via MergeOS admin ledger to `github:<your-login>`.
