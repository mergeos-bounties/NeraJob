"""The Muse jobs API adapter with offline fallback."""

from __future__ import annotations

import hashlib
import os

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper

_OFFLINE = [
    (
        "Product Engineer",
        "Muse Demo Co",
        "New York / Remote",
        ["python", "product", "api"],
        "https://www.themuse.com/jobs/demo-product-engineer",
    ),
    (
        "Data Analyst",
        "Insight Labs",
        "Remote",
        ["sql", "python", "analytics"],
        "https://www.themuse.com/jobs/demo-data-analyst",
    ),
    (
        "Platform SRE",
        "Harbor Cloud",
        "Remote",
        ["sre", "kubernetes", "python"],
        "https://www.themuse.com/jobs/demo-platform-sre",
    ),
]


class TheMuseScraper(BaseScraper):
    """https://www.themuse.com/developers/api/v2"""

    name = "themuse"
    API_URL = "https://www.themuse.com/api/public/jobs"

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        if os.getenv("NERAJOB_THEMUSE_OFFLINE", "").strip().lower() in {"1", "true", "yes"}:
            return self._offline(query, limit)
        headers = {"User-Agent": user_agent(), "Accept": "application/json"}
        params = {"page": 1, "descending": "true"}
        try:
            with httpx.Client(timeout=http_timeout(), headers=headers, follow_redirects=True) as client:
                response = client.get(self.API_URL, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return self._offline(query, limit)

        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list):
            return self._offline(query, limit)

        q = query.strip().lower()
        jobs: list[JobPosting] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            title = str(item.get("name") or item.get("title") or "").strip()
            company = ""
            comps = item.get("company") or {}
            if isinstance(comps, dict):
                company = str(comps.get("name") or "")
            if not title:
                continue
            locs = item.get("locations") or []
            place = ", ".join(
                str(x.get("name") or "") for x in locs if isinstance(x, dict)
            ) or "Remote"
            cats = [str(c.get("name") or "").lower() for c in (item.get("categories") or []) if isinstance(c, dict)]
            hay = f"{title} {company} {place} {' '.join(cats)} {item.get('contents', '')}".lower()
            if q and q not in hay:
                continue
            raw_id = str(item.get("id") or title)
            digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]
            jobs.append(
                JobPosting(
                    id=f"themuse-{digest}",
                    source=self.name,
                    title=title,
                    company=company or "Unknown",
                    location=place,
                    url=str(item.get("refs", {}).get("landing_page") if isinstance(item.get("refs"), dict) else "")
                    or f"https://www.themuse.com/jobs/{raw_id}",
                    description=str(item.get("contents") or "")[:4000],
                    tags=cats[:20],
                    remote="remote" in place.lower(),
                    raw={"themuse_id": raw_id},
                )
            )
            if len(jobs) >= limit:
                break
        return jobs if jobs else self._offline(query, limit)

    def _offline(self, query: str, limit: int) -> list[JobPosting]:
        q = query.strip().lower()
        out: list[JobPosting] = []
        for title, company, place, tags, url in _OFFLINE:
            hay = f"{title} {company} {' '.join(tags)}".lower()
            if q and q not in hay:
                continue
            digest = hashlib.sha1(f"{self.name}:{title}".encode()).hexdigest()[:12]
            out.append(
                JobPosting(
                    id=f"themuse-{digest}",
                    source=self.name,
                    title=title,
                    company=company,
                    location=place,
                    url=url,
                    description=f"{title} at {company} (offline The Muse sample).",
                    tags=tags,
                    remote="remote" in place.lower(),
                    raw={"offline": True},
                )
            )
            if len(out) >= limit:
                break
        return out
