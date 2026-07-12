# NeraJob

**NeraJob** is a Python toolkit that:

1. **Scans job listings** from many public job boards and career sites (pluggable scrapers)
2. **Builds and maintains your CV** from profile data + matched roles
3. **Helps you apply** with tailored cover notes, checklists, and export packages

This repository lives under the [mergeos-bounties](https://github.com/mergeos-bounties) organization and is the product source of truth for the NeraJob tool.

## Stack

- Python 3.11+
- CLI via `typer`
- HTTP via `httpx`
- HTML parsing via `beautifulsoup4` + `lxml`
- Local storage: JSON under `data/`

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
```

## Common commands

```bash
# Initialize a local profile (CV seed)
nerajob profile init

# Edit data/profile.json then validate
nerajob profile show

# Scan sample / remote job sources
nerajob scan --query "python backend" --location "remote" --limit 20

# Build a CV (Markdown + plain text)
nerajob cv build --target "Backend Engineer"

# Prepare an apply package for one job id
nerajob apply prepare --job-id <id>

# List saved jobs
nerajob jobs list
```

## Architecture

```
src/nerajob/
  cli.py              # Typer CLI entry
  config.py           # paths + settings
  models.py           # Job, Profile, Application models
  storage.py          # JSON persistence under data/
  scrapers/
    base.py           # Scraper protocol
    registry.py       # register built-in scrapers
    sample.py         # offline sample feed for demos/tests
    remoteok.py       # RemoteOK public API adapter (example live source)
  cv/
    builder.py        # CV generation from profile + target role
  apply/
    assistant.py      # cover note + checklist + package export
```

### Adding a new job site

1. Create `src/nerajob/scrapers/mysite.py` implementing `BaseScraper`
2. Register it in `scrapers/registry.py`
3. Add tests under `tests/`

Respect each site’s terms of service, robots.txt, and rate limits. Prefer official APIs when available.

## Data layout

```
data/
  profile.json        # your profile / CV source of truth
  jobs.json           # scanned jobs cache
  applications/       # per-job apply packages
```

`data/` is gitignored except for example fixtures.

## Development

```bash
pytest -q
ruff check src tests
```

## MergeOS bounties (claim MRG)

NeraJob issues labeled `bounty` pay **MRG** via MergeOS after merge.

1. Read [docs/BOUNTY.md](docs/BOUNTY.md)
2. Pick an open issue with `reward:*-mrg`
3. Claim on the issue + on MergeOS [Claim Token #1](https://github.com/mergeos-bounties/mergeos/issues/1)
4. Open a PR to this repo (`Fixes #N`)
5. Maintainer merges and credits `github:<you>` on the MergeOS ledger (25/50/100/200 scale)

High-demand work: **job board scrapers** (see open issues tagged `scraper`).

## MergeOS

NeraJob is a sister project under [mergeos-bounties](https://github.com/mergeos-bounties). Parent OS: [mergeos-bounties/mergeos](https://github.com/mergeos-bounties/mergeos).

## License

MIT
