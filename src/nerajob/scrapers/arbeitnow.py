"""Arbeitnow public jobs API adapter with offline fallback."""

from __future__ import annotations

import hashlib
import os

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper

_OFFLINE = [
    (
        "Backend Engineer (Python)",
        "Arbeitnow Demo GmbH",
        "Berlin / Remote",
        ["python", "django", "remote"],
        "https://www.arbeitnow.com/view/demo-python-backend",
    ),
    (
        "DevOps Engineer",
        "Cloud North",
        "Remote EU",
        ["kubernetes", "terraform", "aws"],
        "https://www.arbeitnow.com/view/demo-devops",
    ),
    (
        "Security Engineer",
        "Shield EU",
        "Remote",
        ["security", "python", "appsec"],
        "https://www.arbeitnow.com/view/demo-security",
    ),
]


class ArbeitnowScraper(BaseScraper):
    """https://www.arbeitnow.com/api/job-board-api"""

    name = "arbeitnow"
    API_URL = "https://www.arbeitnow.com/api/job-board-api"

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        if os.getenv("NERAJOB_ARBEITNOW_OFFLINE", "").strip().lower() in {"1", "true", "yes"}:
            return self._offline(query, limit)
        headers = {"User-Agent": user_agent(), "Accept": "application/json"}
        try:
            with httpx.Client(timeout=http_timeout(), headers=headers, follow_redirects=True) as client:
                response = client.get(self.API_URL)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return self._offline(query, limit)

        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            return self._offline(query, limit)

        q = query.strip().lower()
        loc = location.strip().lower()
        jobs: list[JobPosting] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            company = str(item.get("company_name") or "").strip()
            if not title:
                continue
            tags = [str(t).lower() for t in (item.get("tags") or []) if t]
            place = str(item.get("location") or "Remote")
            hay = f"{title} {company} {place} {' '.join(tags)} {item.get('description', '')}".lower()
            if q and q not in hay:
                continue
            if loc and loc not in place.lower() and "remote" not in place.lower():
                continue
            raw_id = str(item.get("slug") or item.get("url") or title)
            digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]
            jobs.append(
                JobPosting(
                    id=f"arbeitnow-{digest}",
                    source=self.name,
                    title=title,
                    company=company or "Unknown",
                    location=place,
                    url=str(item.get("url") or ""),
                    description=str(item.get("description") or "")[:4000],
                    tags=tags[:20],
                    remote="remote" in place.lower(),
                    raw={"slug": raw_id},
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
                    id=f"arbeitnow-{digest}",
                    source=self.name,
                    title=title,
                    company=company,
                    location=place,
                    url=url,
                    description=f"{title} at {company} (offline Arbeitnow sample).",
                    tags=tags,
                    remote="remote" in place.lower(),
                    raw={"offline": True},
                )
            )
            if len(out) >= limit:
                break
        return out
