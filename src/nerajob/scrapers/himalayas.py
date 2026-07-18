"""Himalayas public remote jobs API adapter with offline fallback."""

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
        "Himalayas Demo Co",
        "Remote",
        ["python", "backend", "api"],
        "https://himalayas.app/jobs/senior-python-developer",
    ),
    (
        "Full Stack Engineer",
        "RemoteStack",
        "Worldwide",
        ["react", "node", "typescript", "fullstack"],
        "https://himalayas.app/jobs/full-stack-engineer",
    ),
    (
        "DevOps Engineer",
        "CloudBase Remote",
        "Remote - EU",
        ["kubernetes", "terraform", "aws", "devops"],
        "https://himalayas.app/jobs/devops-engineer",
    ),
]


class HimalayasScraper(BaseScraper):
    """
    Himalayas public remote jobs API.

    Docs: https://himalayas.app/docs/remote-jobs-api
    Browse: https://himalayas.app/jobs/api
    Search: https://himalayas.app/jobs/api/search?query=...
    Free, no API key required.
    """

    name = "himalayas"
    API_URL = "https://himalayas.app/jobs/api"

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        if os.getenv("NERAJOB_HIMALAYAS_OFFLINE", "").strip().lower() in {"1", "true", "yes"}:
            return self._offline(query, limit)

        headers = {"User-Agent": user_agent(), "Accept": "application/json"}
        params: dict[str, str | int] = {"limit": min(max(limit, 1), 100), "offset": 0}

        try:
            with httpx.Client(timeout=http_timeout(), headers=headers, follow_redirects=True) as client:
                response = client.get(self.API_URL, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return self._offline(query, limit)

        jobs_raw = payload.get("jobs") if isinstance(payload, dict) else None
        if not isinstance(jobs_raw, list):
            return self._offline(query, limit)

        q = query.strip().lower()
        loc = location.strip().lower()
        jobs: list[JobPosting] = []

        for item in jobs_raw:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            company = str(item.get("company") or "").strip()
            if isinstance(company, dict):
                company = str(company.get("name") or "")
            if not title:
                continue

            company_obj = item.get("company")
            if isinstance(company_obj, dict):
                company = str(company_obj.get("name") or "")

            tags_raw = item.get("categories") or []
            if isinstance(tags_raw, list):
                tags = [str(t).lower() for t in tags_raw if t]
            else:
                tags = []

            place = str(item.get("location") or item.get("country") or "Remote")
            description = str(item.get("description") or item.get("excerpt") or "")
            salary_min = item.get("salaryMin")
            salary_max = item.get("salaryMax")
            salary_currency = item.get("salaryCurrency") or ""
            salary = ""
            if salary_min and salary_max:
                salary = f"{salary_min}-{salary_max} {salary_currency}".strip()
            elif salary_min:
                salary = f"{salary_min}+ {salary_currency}".strip()
            elif salary_max:
                salary = f"up to {salary_max} {salary_currency}".strip()

            hay = f"{title} {company} {place} {' '.join(tags)} {description}".lower()
            if q and q not in hay:
                continue
            if loc and loc not in place.lower() and "remote" not in place.lower():
                continue

            raw_id = str(item.get("id") or item.get("slug") or title)
            digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]
            jobs.append(
                JobPosting(
                    id=f"himalayas-{digest}",
                    source=self.name,
                    title=title,
                    company=company or "Unknown",
                    location=place or "Remote",
                    url=str(item.get("url") or item.get("applyUrl") or ""),
                    description=description[:4000],
                    tags=tags[:20],
                    salary=salary,
                    remote=True,
                    raw={"himalayas_id": raw_id},
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
                    id=f"himalayas-{digest}",
                    source=self.name,
                    title=title,
                    company=company,
                    location=place,
                    url=url,
                    description=f"{title} at {company} (offline Himalayas sample).",
                    tags=tags,
                    remote=True,
                    raw={"offline": True},
                )
            )
            if len(out) >= limit:
                break
        return out
