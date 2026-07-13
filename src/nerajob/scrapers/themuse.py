"""
The Muse scraper — job board API.

Source: https://www.themuse.com/api/public
Public API — no auth required for basic search.
"""
from __future__ import annotations

import hashlib
import re

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper


class TheMuseScraper(BaseScraper):
    """
    The Muse public jobs API adapter.

    API: GET https://www.themuse.com/api/public/jobs
    Params: page, desc, location, category, company_size
    No auth required.

    ToS: free for personal/non-commercial use.
    """

    name = "themuse"
    API_URL = "https://www.themuse.com/api/public/jobs"

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
        page = 0

        try:
            with httpx.Client(timeout=http_timeout(), headers=headers, follow_redirects=True) as client:
                while len(jobs) < limit:
                    params: dict[str, int | str] = {
                        "page": page,
                        "descending": "true",
                    }
                    if query:
                        params["q"] = query
                    if location:
                        params["location"] = location

                    resp = client.get(self.API_URL, params=params)
                    resp.raise_for_status()
                    payload = resp.json()

                    raw_jobs = payload.get("results") or []
                    if not raw_jobs:
                        break

                    for item in raw_jobs:
                        posting = self._parse(item)
                        if posting:
                            # Client-side filter
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
            return []

        return jobs[:limit]

    def _parse(self, item: dict) -> JobPosting | None:
        title = str(item.get("name") or item.get("title") or "").strip()
        company_name = (
            item.get("company", {}).get("name")
            if isinstance(item.get("company"), dict)
            else str(item.get("company") or item.get("company_name") or "Unknown")
        ).strip()
        if not title:
            return None

        company = str(company_name)

        url = str(item.get("refs", {}).get("landing_page") or item.get("url") or "")

        # Build id from id field
        raw_id = str(item.get("id") or title)
        digest = hashlib.sha1(f"{self.name}:{raw_id}:{company}".encode()).hexdigest()[:12]

        tags: list[str] = []

        categories = item.get("categories") or []
        for c in categories:
            tag = str(c).strip()
            if tag and tag not in tags:
                tags.append(tag)

        levels = item.get("levels") or []
        for lvl in levels:
            tag = str(lvl.get("name") if isinstance(lvl, dict) else lvl).strip()
            if tag and tag not in tags:
                tags.append(tag)

        locations = item.get("locations") or []
        location_parts = [
            str(loc.get("name") if isinstance(loc, dict) else loc) for loc in locations
        ]
        location_str = ", ".join(lp for lp in location_parts if lp) or "Remote"

        remote = any("remote" in loc.lower() for loc in location_parts) or not location_parts

        description = _strip_html(
            str(item.get("contents") or item.get("description") or "")[:4000]
        )

        salary = ""
        compensation = item.get("compensation") or {}
        if compensation:
            salary = str(compensation.get("currency", "")) + " " + str(
                compensation.get("visible") or ""
            )

        return JobPosting(
            id=f"themuse-{digest}",
            source=self.name,
            title=title,
            company=company,
            location=location_str,
            url=url,
            description=description[:4000],
            tags=tags[:20],
            salary=salary.strip(),
            remote=remote,
            raw={
                "themuse_id": raw_id,
                "levels": [lv.get("name") if isinstance(lv, dict) else str(lv) for lv in levels],
                "categories": categories,
            },
        )


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", text).strip()