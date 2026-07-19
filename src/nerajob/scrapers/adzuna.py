"""Adzuna Jobs API scraper with multi-country support.

Requirements:
- Env: ADZUNA_APP_ID, ADZUNA_APP_KEY
- CLI: --country flag (us, gb, de, au, in, etc.)
- Tests: mock HTTP responses for 2+ countries
- Docs: free developer signup guide

Source: https://developer.adzuna.com/
"""

from __future__ import annotations

import logging
import os
from typing import ClassVar
from urllib.error import URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting, to_iso_date_str
from nerajob.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# ISO 3166-1 alpha-2 → Adzuna country code mapping
# https://developer.adzuna.com/activedocs#!/adzuna/search
_COUNTRY_MAP: dict[str, str] = {
    "us": "us", "gb": "gb", "de": "de", "au": "au",
    "in": "in", "ca": "ca", "fr": "fr", "nl": "nl",
    "br": "br", "ru": "ru", "za": "za", "pl": "pl",
    "sg": "sg", "it": "it", "es": "es", "mx": "mx",
    "at": "at", "be": "be", "ch": "ch", "se": "se",
    "no": "no", "nz": "nz", "ie": "ie", "pt": "pt",
    "ae": "ae", "hk": "hk", "my": "my", "ph": "ph",
    "th": "th", "vn": "vn", "id": "id", "jp": "jp",
    "kr": "kr", "tr": "tr", "eg": "eg", "ng": "ng",
    "ke": "ke", "gh": "gh", "ma": "ma", "ar": "ar",
    "cl": "cl", "pe": "pe", "co": "co", "ve": "ve",
}

_ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs"


class AdzunaScraper(BaseScraper):
    """Scraper for Adzuna Jobs API.

    Sign up for free at https://developer.adzuna.com/ to get:
    - ADZUNA_APP_ID
    - ADZUNA_APP_KEY
    """

    name: ClassVar[str] = "adzuna"

    def __init__(self, country: str = "us"):
        self._country = self._normalize_country(country)
        self._app_id = os.getenv("ADZUNA_APP_ID", "")
        self._app_key = os.getenv("ADZUNA_APP_KEY", "")

    @staticmethod
    def _normalize_country(country: str) -> str:
        c = country.strip().lower()
        if c in _COUNTRY_MAP:
            return c
        raise ValueError(
            f"Unsupported country: {country}. "
            f"Supported: {', '.join(sorted(_COUNTRY_MAP))}"
        )

    @property
    def country(self) -> str:
        return self._country

    @property
    def _has_credentials(self) -> bool:
        return bool(self._app_id) and bool(self._app_key)

    def _build_url(
        self, query: str, location: str = "", page: int = 1, results_per_page: int = 20
    ) -> str:
        """Build Adzuna API search URL."""
        what = quote_plus(query)
        where = quote_plus(location) if location else ""
        return (
            f"{_ADZUNA_BASE}/{self._country}/search/{page}"
            f"?app_id={self._app_id}&app_key={self._app_key}"
            f"&results_per_page={min(results_per_page, 50)}"
            f"&what={what}"
            f"{'&where=' + where if where else ''}"
            f"&content-type=application/json"
        )

    def _parse_job(self, raw: dict) -> JobPosting:
        """Parse a single Adzuna API result into a JobPosting."""
        created = raw.get("created", "")
        try:
            date_posted = to_iso_date_str(created) if created else ""
        except Exception:
            date_posted = created

        return JobPosting(
            id=f"adzuna-{self._country}-{raw.get('id', '')}",
            title=raw.get("title", "Untitled"),
            company=raw.get("company", {}).get("display_name", "Unknown"),
            location=raw.get("location", {}).get("display_name", ""),
            description=raw.get("description", "")[:5000],
            url=raw.get("redirect_url", ""),
            source=self.name,
            salary_min=raw.get("salary_min"),
            salary_max=raw.get("salary_max"),
            salary_currency=raw.get("salary_currency"),
            contract_type=raw.get("contract_type", ""),
            date_posted=date_posted,
        )

    def search(
        self, query: str, location: str = "", limit: int = 20
    ) -> list[JobPosting]:
        """Search Adzuna Jobs API.

        Args:
            query: Search keywords (e.g., "python developer").
            location: City/region filter (empty = nationwide).
            limit: Max results to return (per-page capped at 50).

        Returns:
            List of JobPosting objects, or empty list on error.
        """
        if not self._has_credentials:
            logger.warning(
                "Adzuna: ADZUNA_APP_ID / ADZUNA_APP_KEY not set. "
                "Get free keys at https://developer.adzuna.com/"
            )
            return []

        results: list[JobPosting] = []
        page = 1
        per_page = min(limit, 50)

        while len(results) < limit:
            url = self._build_url(query, location, page, per_page)
            try:
                req = Request(url, headers={"User-Agent": user_agent()})
                with urlopen(req, timeout=http_timeout()) as resp:  # noqa: S310
                    data = __import__("json").loads(resp.read())
            except (URLError, TimeoutError, OSError, Exception) as e:
                logger.warning("Adzuna API error: %s", e)
                break
            except ImportError:
                logger.warning("Adzuna: json module unavailable")
                break

            hits = data.get("results", [])
            if not hits:
                break

            for hit in hits:
                try:
                    results.append(self._parse_job(hit))
                except Exception:
                    logger.debug("Skipped malformed Adzuna result", exc_info=True)

            if len(hits) < per_page:
                break
            page += 1

        return results[:limit]
