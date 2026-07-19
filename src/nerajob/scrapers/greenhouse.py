"""Greenhouse public board JSON scraper.

Bounty #11 — 50 MRG

API docs: https://developers.greenhouse.io/job-board.html

Environment:
    GREENHOUSE_BOARD_TOKENS: Comma-separated board tokens
        e.g. "airbnb,spotify,twitch"
"""

from __future__ import annotations

import os
from typing import Any

from nerajob.scrapers.base import BaseScraper, JobResult

GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards"


class GreenhouseScraper(BaseScraper):
    """Scraper for Greenhouse public job boards."""

    SOURCE_NAME = "greenhouse"

    def __init__(self, board_tokens: list[str] | None = None, **kwargs: Any):
        super().__init__(**kwargs)
        if board_tokens is not None:
            self.board_tokens = board_tokens
        else:
            env_tokens = os.environ.get("GREENHOUSE_BOARD_TOKENS", "airbnb,spotify,twitch")
            self.board_tokens = [t.strip() for t in env_tokens.split(",") if t.strip()]

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
        """Fetch jobs from Greenhouse boards.

        Iterates configured board tokens and aggregates results.
        """
        if not self.board_tokens:
            return self._offline_sample(query)

        results: list[JobResult] = []
        for token in self.board_tokens:
            if len(results) >= limit:
                break
            jobs = self._fetch_board(token, query, location)
            for job in jobs:
                results.append(job)
                if len(results) >= limit:
                    break
        return results

    def _fetch_board(
        self, board_token: str, query: str, location: str
    ) -> list[JobResult]:
        """Fetch all jobs from a single Greenhouse board."""
        url = f"{GREENHOUSE_API_BASE}/{board_token}/jobs"
        try:
            data = self.http_get(url)
        except Exception:
            return []
        jobs_raw = data.get("jobs", [])

        results: list[JobResult] = []
        for raw in jobs_raw:
            job = self._map_job(raw, board_token)
            if self._matches_query(job, query, location):
                results.append(job)
        return results

    # ------------------------------------------------------------------
    # Mapping & filtering
    # ------------------------------------------------------------------

    def _map_job(self, raw: dict[str, Any], board_token: str) -> JobResult:
        location = self._extract_location(raw)
        return JobResult(
            source=f"greenhouse:{board_token}",
            title=raw.get("title", ""),
            company=raw.get("name", board_token.title()),
            location=location,
            url=raw.get("absolute_url", f"https://boards.greenhouse.io/{board_token}/jobs/{raw.get('id', '')}"),
            description=raw.get("content", ""),
            tags=self._extract_tags(raw),
            salary=self._extract_salary(raw),
        )

    @staticmethod
    def _extract_location(raw: dict[str, Any]) -> str:
        locs = raw.get("location", {})
        name = locs.get("name", "")
        return name if name else "Remote"

    @staticmethod
    def _extract_tags(raw: dict[str, Any]) -> list[str]:
        tags: list[str] = []
        depts = raw.get("departments", [])
        for d in depts:
            name = d.get("name", "")
            if name:
                tags.append(name)
        offices = raw.get("offices", [])
        for o in offices:
            name = o.get("name", "")
            if name:
                tags.append(name)
        return tags

    @staticmethod
    def _extract_salary(raw: dict[str, Any]) -> str:
        # Greenhouse boards don't always expose salary
        return ""

    def _matches_query(self, job: JobResult, query: str, location: str) -> bool:
        q = query.strip().strip("*")
        if q and q.lower() not in job.title.lower() and q.lower() not in job.description.lower():
            return False
        if location and location.lower() not in job.location.lower():
            return False
        return True

    # ------------------------------------------------------------------
    # Offline fallback
    # ------------------------------------------------------------------

    @staticmethod
    def _offline_sample(query: str) -> list[JobResult]:
        return [
            JobResult(
                source="greenhouse:airbnb",
                title=f"Senior {query.title()} Engineer",
                company="Airbnb",
                location="San Francisco, CA",
                url="https://boards.greenhouse.io/airbnb/jobs/sample-1",
                description=f"Build {query} features at Airbnb scale.",
                tags=["Engineering", "San Francisco"],
                salary="",
            ),
            JobResult(
                source="greenhouse:spotify",
                title=f"{query.title()} Developer",
                company="Spotify",
                location="Stockholm, Sweden",
                url="https://boards.greenhouse.io/spotify/jobs/sample-2",
                description=f"Join Spotify's {query} team.",
                tags=["Product & Engineering", "Stockholm"],
                salary="",
            ),
        ]
