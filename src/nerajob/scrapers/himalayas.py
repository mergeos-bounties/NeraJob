"""Himalayas.app public jobs API adapter (with offline sample fallback)."""

from __future__ import annotations

import hashlib
import os
from typing import Any

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper

# Offline fixtures when network fails or NERAJOB_HIMALAYAS_OFFLINE=1
_OFFLINE = [
    (
        "Senior Python Engineer",
        "TechCorp Remote",
        "Remote",
        ["python", "django", "aws"],
        "https://himalayas.app/jobs/123-python-engineer",
    ),
    (
        "Frontend Developer (React)",
        "WebSolutions Inc",
        "Europe",
        ["javascript", "react", "typescript"],
        "https://himalayas.app/jobs/456-frontend-react",
    ),
    (
        "DevOps Engineer",
        "CloudFirst Ltd",
        "North America",
        ["docker", "kubernetes", "aws"],
        "https://himalayas.app/jobs/789-devops-engineer",
    ),
]


class HimalayasScraper(BaseScraper):
    """Himalayas.app public jobs API.

    Docs: https://himalayas.app/jobs/api
    Endpoint: https://himalayas.app/jobs/api
    """

    name = "himalayas"
    API_URL = "https://himalayas.app/jobs/api"

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        if os.getenv("NERAJOB_HIMALAYAS_OFFLINE", "").strip() in {"1", "true", "yes"}:
            return self._offline(query, limit)

        headers = {
            "User-Agent": user_agent(),
            "Accept": "application/json",
        }
        try:
            with httpx.Client(timeout=http_timeout(), headers=headers, follow_redirects=True) as client:
                params = {"limit": min(limit, 50)}  # API max seems reasonable
                if query:
                    params["search"] = query
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
            company = str(item.get("companyName") or "").strip()
            if not title:
                continue

            # Location handling - Himalayas uses locationRestrictions array
            location_str = ", ".join(item.get("locationRestrictions", [])) or "Remote"
            if loc and loc not in location_str.lower():
                continue

            # Query matching across title, company, description, categories
            description = str(item.get("excerpt") or "")
            categories = " ".join(str(c) for c in item.get("categories", []))
            hay = f"{title} {company} {description} {categories}".lower()
            if q and q not in hay:
                continue

            url = str(item.get("url") or "")
            raw_id = str(item.get("id") or title)
            digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]

            jobs.append(
                JobPosting(
                    id=f"himalayas-{digest}",
                    source=self.name,
                    title=title,
                    company=company or "Unknown",
                    location=location_str or "Remote",
                    url=url,
                    description=description[:4000],
                    tags=[c.lower() for c in item.get("categories", [])][:20],
                    remote="remote" in location_str.lower() or not location_str,
                    raw={
                        "himalayas_id": raw_id,
                        "companySlug": item.get("companySlug"),
                        "employmentType": item.get("employmentType"),
                        "salaryPeriod": item.get("salaryPeriod"),
                        "minSalary": item.get("minSalary"),
                        "maxSalary": item.get("maxSalary"),
                        "currency": item.get("currency"),
                        "seniority": item.get("seniority"),
                    },
                )
            )
            if len(jobs) >= limit:
                break

        return jobs if jobs else self._offline(query, limit)

    def _offline(self, query: str, limit: int) -> list[JobPosting]:
        q = query.strip().lower()
        loc = location.strip().lower() if 'location' in locals() else ""
        out: list[JobPosting] = []
        for title, company, place, tags, url in _OFFLINE:
            hay = f"{title} {company} {' '.join(tags)} {place}".lower()
            if q and q not in hay:
                continue
            if loc and loc not in place.lower():
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
                    remote="remote" in place.lower(),
                    raw={"offline": True},
                )
            )
            if len(out) >= limit:
                break
        return out