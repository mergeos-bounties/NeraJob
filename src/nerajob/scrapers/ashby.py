"""Ashby public job board adapter for NeraJob."""

from __future__ import annotations

import hashlib
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper
from nerajob.config import http_timeout, user_agent


class AshbyScraper(BaseScraper):
    """
    Ashby public job board adapter.

    Ashby provides a public API per company:
        https://api.ashbyhq.com/posting-api/job-board/<board-identifier>

    Usage::

        scraper = AshbyScraper(board_id="company-name")
        scraper.search(query="python", limit=10)

    Bounty: https://github.com/mergeos-bounties/NeraJob/issues/13
    """

    name = "ashby"
    BASE_URL = "https://api.ashbyhq.com/posting-api/job-board/{board_id}"

    def __init__(self, board_id: str | None = None) -> None:
        self.board_id = board_id

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        jobs_data = self._fetch()
        q = query.strip().lower()
        loc = location.strip().lower()
        results: list[JobPosting] = []

        for item in jobs_data:
            if len(results) >= limit:
                break

            job = self._normalize(item)
            hay = f"{job.title} {job.company} {job.description} {' '.join(job.tags)}".lower()

            if q and q not in hay:
                continue
            if loc and loc not in job.location.lower():
                continue

            results.append(job)

        return results

    def _fetch(self) -> list[dict]:
        if not self.board_id:
            return self._sample_data()

        url = self.BASE_URL.format(board_id=self.board_id)
        req = Request(url, headers={"User-Agent": user_agent(), "Accept": "application/json"})

        try:
            with urlopen(req, timeout=http_timeout()) as resp:
                data = json.loads(resp.read().decode())
                return data.get("jobs", [])
        except (HTTPError, URLError, json.JSONDecodeError, OSError):
            return []

    def _normalize(self, raw: dict) -> JobPosting:
        title = raw.get("title", "") or ""
        company = (raw.get("organization") or {}).get("name", "") or ""
        location = raw.get("location", "") or "Remote"
        url = raw.get("jobUrl", "") or ""
        desc = (raw.get("descriptionHtml") or "")[:4000]
        raw_id = raw.get("id") or title
        digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]
        dept = (raw.get("department") or "") or ""

        return JobPosting(
            id=f"ashby-{digest}",
            source=self.name,
            title=title,
            company=company or "Unknown",
            location=location,
            url=url,
            description=_strip_html(desc),
            tags=[dept] if dept else [],
            salary="",
            remote="remote" in location.lower(),
            raw={"ashby_id": raw_id, "board_id": self.board_id},
        )

    def _sample_data(self) -> list[dict]:
        return [
            {
                "id": "sample-1",
                "title": "Senior Software Engineer",
                "organization": {"name": "TechCorp"},
                "location": "Remote, US",
                "descriptionHtml": "<p>Python backend development</p>",
                "jobUrl": "https://jobs.ashbyhq.com/techcorp/123",
                "department": "Engineering",
            },
        ]


def _strip_html(value: str) -> str:
    import re
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", text).strip()
