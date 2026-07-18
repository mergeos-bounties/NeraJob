"""Adzuna jobs search API adapter with offline fallback.

Requires ADZUNA_APP_ID and ADZUNA_APP_KEY for live search.
https://developer.adzuna.com/overview
"""

from __future__ import annotations

import hashlib
import os

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper

_OFFLINE = [
    (
        "Senior Python Developer",
        "Adzuna Demo Ltd",
        "London, UK",
        ["python", "django", "postgresql"],
        "https://www.adzuna.co.uk/jobs/demo/senior-python-dev",
    ),
    (
        "Full Stack Engineer",
        "TechStack Global",
        "Berlin, Germany",
        ["javascript", "react", "node", "typescript"],
        "https://www.adzuna.co.uk/jobs/demo/fullstack-engineer",
    ),
    (
        "Data Engineer",
        "DataPipeline Inc",
        "Remote / UK",
        ["python", "spark", "airflow", "etl"],
        "https://www.adzuna.co.uk/jobs/demo/data-engineer",
    ),
]


class AdzunaScraper(BaseScraper):
    """
    Adzuna jobs search API.

    Docs: https://developer.adzuna.com/overview
    Endpoint: https://api.adzuna.com/v1/api/jobs/{country}/search/{page}
    Requires ADZUNA_APP_ID and ADZUNA_APP_KEY env vars for live search.
    Without env, uses offline sample postings (tests/demos).
    """

    name = "adzuna"
    API_BASE = "https://api.adzuna.com/v1/api/jobs"

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        app_id = os.getenv("ADZUNA_APP_ID", "").strip()
        app_key = os.getenv("ADZUNA_APP_KEY", "").strip()
        if not app_id or not app_key:
            return self._offline(query, limit)

        country = os.getenv("ADZUNA_COUNTRY", "gb").strip()
        params: dict[str, str | int] = {
            "app_id": app_id,
            "app_key": app_key,
            "what": query,
            "results_per_page": min(max(limit, 1), 50),
            "content_type": "application/json",
        }
        if location:
            params["where"] = location

        url = f"{self.API_BASE}/{country}/search/1"
        headers = {"User-Agent": user_agent(), "Accept": "application/json"}

        try:
            with httpx.Client(timeout=http_timeout(), headers=headers, follow_redirects=True) as client:
                response = client.get(url, params=params)
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
            title = str(item.get("title") or "").strip()
            company = str(item.get("company", {}).get("display_name") if isinstance(item.get("company"), dict) else item.get("company") or "").strip()
            if not title:
                continue

            place = str(item.get("location", {}).get("display_name") if isinstance(item.get("location"), dict) else item.get("location") or "Remote")
            tags = [str(t).lower() for t in (item.get("category", {}).get("label", "") if isinstance(item.get("category"), dict) else str(item.get("category") or "")).split("/") if t.strip()]

            description = str(item.get("description") or "")
            url = str(item.get("redirect_url") or item.get("url") or "")
            salary_min = item.get("salary_min")
            salary_max = item.get("salary_max")
            salary = ""
            if salary_min is not None and salary_max is not None:
                salary = f"{salary_min:.0f}-{salary_max:.0f} {item.get('salary_currency', 'GBP')}"
            elif salary_min is not None:
                salary = f"{salary_min:.0f}+ {item.get('salary_currency', 'GBP')}"
            elif salary_max is not None:
                salary = f"up to {salary_max:.0f} {item.get('salary_currency', 'GBP')}"

            hay = f"{title} {company} {place} {' '.join(tags)} {description}".lower()
            if q and q not in hay:
                continue

            raw_id = str(item.get("id") or title)
            digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]
            jobs.append(
                JobPosting(
                    id=f"adzuna-{digest}",
                    source=self.name,
                    title=title,
                    company=company or "Unknown",
                    location=place,
                    url=url,
                    description=description[:4000],
                    tags=tags[:20],
                    salary=salary,
                    remote="remote" in place.lower(),
                    raw={"adzuna_id": raw_id},
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
                    id=f"adzuna-{digest}",
                    source=self.name,
                    title=title,
                    company=company,
                    location=place,
                    url=url,
                    description=f"{title} at {company} (offline Adzuna sample).",
                    tags=tags,
                    remote="remote" in place.lower(),
                    raw={"offline": True},
                )
            )
            if len(out) >= limit:
                break
        return out
