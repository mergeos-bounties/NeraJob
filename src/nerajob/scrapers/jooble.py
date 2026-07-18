"""Jooble public API adapter for NeraJob."""

from __future__ import annotations

import hashlib
import os

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper


class JoobleScraper(BaseScraper):
    """
    Jooble job search API adapter.

    POST https://jooble.org/api/API_KEY
    Expects NERAJOB_JOOBLE_API_KEY env var.

    Bounty: https://github.com/mergeos-bounties/NeraJob/issues/15
    """

    name = "jooble"
    BASE_URL = "https://jooble.org/api/{api_key}"

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        api_key = os.getenv("NERAJOB_JOOBLE_API_KEY")
        if not api_key:
            return []

        url = self.BASE_URL.format(api_key=api_key)
        payload: dict[str, str | int] = {"keywords": query}
        if location:
            payload["location"] = location

        results: list[JobPosting] = []
        page = 1
        headers = {"User-Agent": user_agent(), "Content-Type": "application/json"}

        try:
            with httpx.Client(timeout=http_timeout(), headers=headers, follow_redirects=True) as client:
                while len(results) < limit:
                    payload["page"] = page
                    response = client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()

                    jobs = data.get("jobs") if isinstance(data, dict) else None
                    if not isinstance(jobs, list):
                        break

                    for item in jobs:
                        if len(results) >= limit:
                            break
                        job = self._normalize(query, item)
                        results.append(job)

                    total_count = data.get("totalCount", 0)
                    if not isinstance(total_count, (int, float)):
                        break
                    if page * len(jobs) >= total_count:
                        break
                    page += 1
        except Exception:
            return results

        return results

    def _normalize(self, query: str, raw: dict) -> JobPosting:
        title = (raw.get("title") or "").strip()
        company = (raw.get("company") or "").strip()
        location = (raw.get("location") or "").strip() or "Remote"
        url = (raw.get("link") or raw.get("url") or "").strip()
        snippet = (raw.get("snippet") or raw.get("description") or "").strip()
        salary = (raw.get("salary") or "").strip()

        raw_id = raw.get("id") or raw.get("title") or title
        digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]

        return JobPosting(
            id=f"jooble-{digest}",
            source=self.name,
            title=title,
            company=company or "Unknown",
            location=location,
            url=url,
            description=snippet[:4000],
            tags=[],
            salary=salary,
            remote="remote" in location.lower(),
            raw={"query": query, "jooble_id": raw_id},
        )
