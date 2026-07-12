from __future__ import annotations

import os

from nerajob.scrapers.arbeitnow import ArbeitnowScraper
from nerajob.scrapers.ashby import AshbyScraper
from nerajob.scrapers.base import BaseScraper
<<<<<<< HEAD
from nerajob.scrapers.jobicy import JobicyScraper
=======
from nerajob.scrapers.himalayas import HimalayasScraper  # <-- NUEVO IMPORT
>>>>>>> d9ce0b7 (feat: register Himalayas scraper in registry #5)
from nerajob.scrapers.lever import LeverScraper
from nerajob.scrapers.remoteok import RemoteOKScraper
from nerajob.scrapers.remotive import RemotiveScraper
from nerajob.scrapers.sample import SampleScraper
from nerajob.scrapers.smartrecruiters import SmartRecruitersScraper
from nerajob.scrapers.themuse import TheMuseScraper
from nerajob.scrapers.weworkremotely import WeWorkRemotelyScraper


def available_scrapers() -> dict[str, BaseScraper]:
    """
    Built-in scrapers.

    Lever / Ashby board IDs (optional):
      NERAJOB_LEVER_BOARD   e.g. company slug for api.lever.co
      NERAJOB_ASHBY_BOARD   e.g. board id for api.ashbyhq.com
    Without env, those adapters use offline sample postings (tests/demos).

    Remotive: live public API; set NERAJOB_REMOTIVE_OFFLINE=1 to force offline samples.
    Arbeitnow: live public API; set NERAJOB_ARBEITNOW_OFFLINE=1 for offline samples.
    Jobicy: live public API; set NERAJOB_JOBICY_OFFLINE=1 for offline samples.
    We Work Remotely: RSS feed; set NERAJOB_WWR_OFFLINE=1 for offline samples.
    SmartRecruiters: set NERAJOB_SMARTRECRUITERS_COMPANIES to comma-separated company IDs.
    """
    scrapers: list[BaseScraper] = [
        SampleScraper(),
        RemoteOKScraper(),
        RemotiveScraper(),
        ArbeitnowScraper(),
        JobicyScraper(),
        TheMuseScraper(),
        WeWorkRemotelyScraper(),
        LeverScraper(board_name=os.getenv("NERAJOB_LEVER_BOARD") or None),
        AshbyScraper(board_id=os.getenv("NERAJOB_ASHBY_BOARD") or None),
<<<<<<< HEAD
        SmartRecruitersScraper(),
=======
        HimalayasScraper(),  # <-- NUEVO SCRAPER AÑADIDO
>>>>>>> d9ce0b7 (feat: register Himalayas scraper in registry #5)
    ]
    return {s.name: s for s in scrapers}


def get_scraper(name: str) -> BaseScraper:
    scrapers = available_scrapers()
    if name not in scrapers:
        known = ", ".join(sorted(scrapers))
        raise KeyError(f"Unknown scraper {name!r}. Known: {known}")
    return scrapers[name]