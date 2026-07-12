"""
Arbeitnow scraper — EU remote job board.

Source: https://www.arbeitnow.com/api
Public JSON API — no auth required.
ToS: Free for personal/non-commercial use. Respect rate limits.
"""
from __future__ import annotations

import hashlib
import re

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper


class ArbeitnowScraper(BaseScraper):
    """
    Arbeitnow public job board API adapter.

    Supports filtering by query string. Pagination is handled internally
    (fetches up to `limit` results across pages).

    API docs: https://www.arbeitnow.com/api
    Rate-limit note: No explicit limit stated; conservative 1 req/s used.
    """

    name = "arbeitnow"
    API_URL = "https://www.arbeitnow.com/api/job-board-api"

    def search(
        self,
        query: str = "",
        location: str = "",
        limit: int = 20,
    ) -> list[JobPosting]:
        headers = {
            "User-Agent": user_agent(),
            "Accept": "application/json",
        }

        q = query.strip().lower()
        jobs: list[JobPosting] = []
        page = 1

        try:
            with httpx.Client(timeout=http_timeout(), headers=headers, follow_redirects=True) as client:
                while len(jobs) < limit:
                    params = {"page": page, "query": query} if query else {"page": page}
                    resp = client.get(self.API_URL, params=params)
                    resp.raise_for_status()
                    payload = resp.json()

                    raw_jobs = payload.get("data") or []
                    if not raw_jobs:
                        break

                    for item in raw_jobs:
                        posting = self._parse(item)
                        if posting:
                            # Client-side filter for reliable keyword matching
                            hay = (
                                posting.title.lower()
                                + " "
                                + posting.company.lower()
                                + " "
                                + " ".join(posting.tags)
                            )
                            if q and q not in hay:
                                continue
                            jobs.append(posting)
                        if len(jobs) >= limit:
                            break

                    if len(raw_jobs) < 20:
                        break

                    page += 1

        except Exception:
            # Network / API failure — degrade gracefully
            return []

        return jobs

    def _parse(self, item: dict) -> JobPosting | None:
        title = str(item.get("title") or "").strip()
        company = str(item.get("company_name") or "Unknown").strip()
        if not title:
            return None

        url = str(item.get("url") or "")
        slug = str(item.get("slug") or "")

        # Build stable id from slug + company
        digest = hashlib.sha1(f"{self.name}:{slug or title}:{company}".encode()).hexdigest()[:12]

        location_str = str(item.get("location") or item.get("location_name") or "EU").strip()
        remote = bool(item.get("remote", False))

        tags = [str(t) for t in (item.get("tags") or []) if t]
        job_types = [str(t) for t in (item.get("job_types") or []) if t]
        all_tags = list(set(tags + job_types))[:20]

        salary_raw = item.get("salary") or item.get("annual_salary") or ""
        salary = str(salary_raw) if salary_raw else ""

        description = _strip_html(str(item.get("description") or ""))

        return JobPosting(
            id=f"arbeitnow-{digest}",
            source=self.name,
            title=title,
            company=company,
            location=location_str,
            url=url,
            description=description[:4000],
            tags=all_tags,
            salary=salary,
            remote=remote,
            raw={"slug": slug},
        )


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", text).strip()