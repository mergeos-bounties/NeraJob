"""Lever public job board adapter for NeraJob."""

from __future__ import annotations

import hashlib
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper
from nerajob.config import http_timeout, user_agent


class LeverScraper(BaseScraper):
    """
    Lever public job board adapter.

    Lever provides a JSON feed at:
        https://api.lever.co/v0/postings/<board-name>?mode=json

    Usage::

        scraper = LeverScraper(board_name="company-name")
        scraper.search(query="design", limit=10)

    Bounty: https://github.com/mergeos-bounties/NeraJob/issues/12
    """

    name = "lever"
    BASE_URL = "https://api.lever.co/v0/postings/{board}?mode=json"

    def __init__(self, board_name: str | None = None) -> None:
        self.board_name = board_name

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        jobs_data = self._fetch()
        q = query.strip().lower()
        loc = location.strip().lower()
        results: list[JobPosting] = []

        for item in jobs_data:
            if len(results) >= limit:
                break

            job = self._normalize(item)
            hay = f"{job.title} {job.description} {' '.join(job.tags)}".lower()

            if q and q not in hay:
                continue
            if loc and loc not in job.location.lower():
                continue

            results.append(job)

        return results

    def _fetch(self) -> list[dict]:
        if not self.board_name:
            return self._sample_data()

        url = self.BASE_URL.format(board=self.board_name)
        req = Request(url, headers={"User-Agent": user_agent(), "Accept": "application/json"})

        try:
            with urlopen(req, timeout=http_timeout()) as resp:
                return json.loads(resp.read().decode())
        except (HTTPError, URLError, json.JSONDecodeError, OSError):
            return []

    def _normalize(self, raw: dict) -> JobPosting:
        title = raw.get("text", "") or ""
        desc = (raw.get("description", "") or "")[:4000]
        url = raw.get("hostedUrl", "") or ""
        categories = raw.get("categories") or {}
        location = (categories.get("location") or "") or "Remote"
        team = (categories.get("team") or "") or ""
        commitment = (categories.get("commitment") or "") or ""
        raw_id = raw.get("id") or title
        digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]

        return JobPosting(
            id=f"lever-{digest}",
            source=self.name,
            title=title,
            company="",
            location=location,
            url=url,
            description=_strip_html(desc),
            tags=[t for t in [team, commitment] if t],
            salary="",
            remote="remote" in location.lower(),
            raw={"lever_id": raw_id, "board_name": self.board_name},
        )

    def _sample_data(self) -> list[dict]:
        return [
            {
                "id": "abc123",
                "text": "Senior Backend Engineer",
                "description": "<p>Python and Go development</p>",
                "categories": {"location": "Remote", "team": "Engineering", "commitment": "Full-time"},
                "hostedUrl": "https://jobs.lever.co/company/abc123",
            },
        ]


def _strip_html(value: str) -> str:
    import re
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", text).strip()
