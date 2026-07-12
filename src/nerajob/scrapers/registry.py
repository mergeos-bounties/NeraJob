from __future__ import annotations

import os

from nerajob.scrapers.ashby import AshbyScraper
from nerajob.scrapers.base import BaseScraper
from nerajob.scrapers.lever import LeverScraper
from nerajob.scrapers.remoteok import RemoteOKScraper
from nerajob.scrapers.remotive import RemotiveScraper
from nerajob.scrapers.sample import SampleScraper


def available_scrapers() -> dict[str, BaseScraper]:
    """
    Built-in scrapers.

    Lever / Ashby board IDs (optional):
      NERAJOB_LEVER_BOARD   e.g. company slug for api.lever.co
      NERAJOB_ASHBY_BOARD   e.g. board id for api.ashbyhq.com
    Without env, those adapters use offline sample postings (tests/demos).

    Remotive: live public API; set NERAJOB_REMOTIVE_OFFLINE=1 to force offline samples.
    """
    scrapers: list[BaseScraper] = [
        SampleScraper(),
        RemoteOKScraper(),
        RemotiveScraper(),
        LeverScraper(board_name=os.getenv("NERAJOB_LEVER_BOARD") or None),
        AshbyScraper(board_id=os.getenv("NERAJOB_ASHBY_BOARD") or None),
    ]
    return {s.name: s for s in scrapers}


def get_scraper(name: str) -> BaseScraper:
    scrapers = available_scrapers()
    if name not in scrapers:
        known = ", ".join(sorted(scrapers))
        raise KeyError(f"Unknown scraper {name!r}. Known: {known}")
    return scrapers[name]
