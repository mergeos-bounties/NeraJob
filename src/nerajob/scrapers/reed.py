"""Reed.co.uk Jobs API scraper.

Bounty #9 — 50 MRG

API docs: https://reed.co.uk/developer/api-reference

Environment:
    REED_API_KEY: Reed API key (obtain from https://reed.co.uk/developer/account)
"""

from __future__ import annotations

import os
from typing import Any

from nerajob.scrapers.base import BaseScraper, JobResult

REED_BASE_URL = "https://www.reed.co.uk/api/1.0/search"


class ReedScraper(BaseScraper):
    """Scraper for Reed.co.uk job listings via their public API."""

    SOURCE_NAME = "reed"

    def __init__(self, api_key: str | None = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.api_key = api_key or os.environ.get("REED_API_KEY", "")

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def build_params(
        self,
        query: str,
        location: str = "",
        results_per_page: int = 25,
        page: int = 1,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "keywords": query,
            "resultsToTake": results_per_page,
            "page": page,
        }
        if location:
            params["locationName"] = location
        return params

    # ------------------------------------------------------------------
    # BaseScraper interface
    # ------------------------------------------------------------------

    def fetch(
        self,
        query: str,
        *,
        location: str = "",
        limit: int = 25,
        **kwargs: Any,
    ) -> list[JobResult]:
        """Fetch jobs from Reed.co.uk API.

        Falls back to offline/mock data when no API key is configured.
        """
        if not self.api_key:
            return self._offline_sample(query)

        results: list[JobResult] = []
        page = 1
        while len(results) < limit:
            params = self.build_params(
                query, location=location, results_per_page=min(25, limit - len(results)), page=page
            )
            headers = {"Authorization": f"Bearer {self.api_key}"}
            data = self.http_get(REED_BASE_URL, params=params, headers=headers)
            jobs = data.get("results", [])
            if not jobs:
                break
            for job in jobs:
                results.append(self._map_job(job))
                if len(results) >= limit:
                    break
            page += 1
            if len(jobs) < params["resultsToTake"]:
                break
        return results

    # ------------------------------------------------------------------
    # Mapping
    # ------------------------------------------------------------------

    def _map_job(self, raw: dict[str, Any]) -> JobResult:
        return JobResult(
            source=self.SOURCE_NAME,
            title=raw.get("jobTitle", ""),
            company=raw.get("employerName", ""),
            location=raw.get("locationName", ""),
            url=raw.get("jobUrl", ""),
            description=raw.get("jobDescription", ""),
            tags=self._extract_tags(raw),
            salary=self._salary_str(raw),
        )

    @staticmethod
    def _extract_tags(raw: dict[str, Any]) -> list[str]:
        tags: list[str] = []
        cat = raw.get("category", "")
        if cat:
            tags.append(cat)
        contract_type = raw.get("contractType", "")
        if contract_type:
            tags.append(contract_type)
        return tags

    @staticmethod
    def _salary_str(raw: dict[str, Any]) -> str:
        min_sal = raw.get("minimumSalary")
        max_sal = raw.get("maximumSalary")
        currency = raw.get("currency", "GBP")
        if min_sal and max_sal:
            return f"{currency} {min_sal}-{max_sal}"
        if min_sal:
            return f"{currency} {min_sal}+"
        return ""

    # ------------------------------------------------------------------
    # Offline fallback
    # ------------------------------------------------------------------

    @staticmethod
    def _offline_sample(query: str) -> list[JobResult]:
        return [
            JobResult(
                source="reed",
                title=f"Software Engineer - {query.title()}",
                company="TechCorp UK",
                location="London, UK",
                url="https://www.reed.co.uk/jobs/sample-1",
                description=f"Looking for {query} engineer with 3+ years experience.",
                tags=["IT", "Permanent"],
                salary="GBP 45000-65000",
            ),
            JobResult(
                source="reed",
                title=f"Senior {query.title()} Developer",
                company="Digital Solutions Ltd",
                location="Manchester, UK",
                url="https://www.reed.co.uk/jobs/sample-2",
                description=f"Senior role in {query} development.",
                tags=["IT", "Contract"],
                salary="GBP 500-600/day",
            ),
        ]
