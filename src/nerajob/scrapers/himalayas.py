"""Himalayas.app public jobs API adapter with offline fallback."""

from __future__ import annotations

import hashlib
import os

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper

# Offline sample data: (title, company, location, tags, url)
_OFFLINE = [
    (
        "Frontend Engineer (React/TypeScript)",
        "Nebula Labs",
        "Remote Worldwide",
        ["react", "typescript", "remote", "frontend"],
        "https://himalayas.app/jobs/nebula-labs-frontend-engineer",
    ),
    (
        "Backend Engineer (Go/PostgreSQL)",
        "Stellar Systems",
        "Remote - Americas",
        ["go", "postgresql", "remote", "backend", "kubernetes"],
        "https://himalayas.app/jobs/stellar-systems-backend-engineer",
    ),
    (
        "DevOps Engineer (AWS/Terraform)",
        "Orbit Infrastructure",
        "Remote Worldwide",
        ["aws", "terraform", "kubernetes", "remote", "devops"],
        "https://himalayas.app/jobs/orbit-infrastructure-devops-engineer",
    ),
]


class HimalayasScraper(BaseScraper):
    """https://himalayas.app/jobs/api"""

    name = "himalayas"
    API_URL = "https://himalayas.app/jobs/api"

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        if os.getenv("NERAJOB_HIMALAYAS_OFFLINE", "").strip().lower() in {"1", "true", "yes"}:
            return self._offline(query, limit)
        headers = {"User-Agent": user_agent(), "Accept": "application/json"}
        try:
            with httpx.Client(timeout=http_timeout(), headers=headers, follow_redirects=True) as client:
                response = client.get(self.API_URL)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return self._offline(query, limit)

        data = payload.get("jobs") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            return self._offline(query, limit)

        q = query.strip().lower()
        loc = location.strip().lower()
        jobs: list[JobPosting] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            company = str(item.get("companyName") or "").strip()
            if not title:
                continue
            tags = [str(t).lower() for t in (item.get("categories") or []) if t]
            place = str(item.get("locationRestrictions") or "Remote")
            if isinstance(place, list):
                place = ", ".join(str(x) for x in place if x)
            is_remote = "remote" in place.lower()
            hay = f"{title} {company} {place} {' '.join(tags)} {item.get('excerpt', '')}".lower()
            if q and q not in hay:
                continue
            if loc and loc not in place.lower() and not is_remote:
                continue
            raw_id = str(item.get("companySlug") or item.get("title") or title)
            digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]
            jobs.append(
                JobPosting(
                    id=f"himalayas-{digest}",
                    source=self.name,
                    title=title,
                    company=company or "Unknown",
                    location=place,
                    url=f"https://himalayas.app/companies/{item.get('companySlug', '')}/jobs/{item.get('title', '').lower().replace(' ', '-')}",
                    description=str(item.get("excerpt") or "")[:4000],
                    tags=tags[:20],
                    remote=is_remote,
                    raw={"companySlug": item.get("companySlug")},
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
            # Match if query is empty, or query appears in title/company/tags, or query is a substring of any tag
            if q and q not in hay and not any(q in tag for tag in tags):
                continue
            digest = hashlib.sha1(f"{self.name}:{title}".encode()).hexdigest()[:12]
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