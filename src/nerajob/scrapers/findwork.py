"""Findwork.dev developer jobs API adapter with offline fallback."""

from __future__ import annotations

import hashlib
import os

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper

_OFFLINE = [
    (
        "Backend Python Developer",
        "Findwork Demo Corp",
        "Remote",
        ["python", "django", "postgresql", "rest"],
        "https://findwork.dev/jobs/demo-backend-python",
    ),
    (
        "Frontend Engineer",
        "CodeCraft Inc",
        "Remote / GMT-5",
        ["react", "typescript", "css", "frontend"],
        "https://findwork.dev/jobs/demo-frontend-engineer",
    ),
    (
        "Site Reliability Engineer",
        "Reliable Systems",
        "Remote",
        ["kubernetes", "terraform", "linux", "sre"],
        "https://findwork.dev/jobs/demo-sre",
    ),
]


class FindworkScraper(BaseScraper):
    """
    Findwork.dev developer jobs API.

    Docs: https://findwork.dev/api/jobs/
    Endpoint: https://findwork.dev/api/jobs/
    Set NERAJOB_FINDWORK_KEY for live API access.
    Without env, uses offline sample postings (tests/demos).
    """

    name = "findwork"
    API_URL = "https://findwork.dev/api/jobs/"

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        api_key = os.getenv("NERAJOB_FINDWORK_KEY", "").strip()
        if not api_key:
            return self._offline(query, limit)

        headers = {
            "User-Agent": user_agent(),
            "Accept": "application/json",
            "Authorization": f"Token {api_key}",
        }
        params: dict[str, str | int] = {"search": query, "page": 1}

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
            title = str(item.get("role_name") or item.get("title") or "").strip()
            company = str(item.get("company_name") or "").strip()
            if not title:
                continue

            place = str(item.get("location") or "Remote")
            tags_raw = item.get("keywords") or item.get("tags") or []
            tags = [str(t).lower() for t in tags_raw if t]

            description = str(item.get("text") or item.get("description") or "")
            url = str(item.get("url") or item.get("apply_url") or "")
            salary = str(item.get("salary") or "")

            hay = f"{title} {company} {place} {' '.join(tags)} {description}".lower()
            if q and q not in hay:
                continue

            raw_id = str(item.get("id") or title)
            digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]
            jobs.append(
                JobPosting(
                    id=f"findwork-{digest}",
                    source=self.name,
                    title=title,
                    company=company or "Unknown",
                    location=place,
                    url=url,
                    description=description[:4000],
                    tags=tags[:20],
                    salary=salary,
                    remote="remote" in place.lower(),
                    raw={"findwork_id": raw_id},
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
            digest = hashlib.sha1(f"{self.name}:{title}:{company}".encode()).hexdigest()[:12]
            out.append(
                JobPosting(
                    id=f"findwork-{digest}",
                    source=self.name,
                    title=title,
                    company=company,
                    location=place,
                    url=url,
                    description=f"{title} at {company} (offline Findwork sample).",
                    tags=tags,
                    remote=True,
                    raw={"offline": True},
                )
            )
            if len(out) >= limit:
                break
        return out
