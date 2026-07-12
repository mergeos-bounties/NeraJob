"""Remotive public jobs API adapter (with offline sample fallback)."""

from __future__ import annotations

import hashlib
import os

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper

# Offline fixtures when network fails or NERAJOB_REMOTIVE_OFFLINE=1
_OFFLINE = [
    (
        "Python API Engineer",
        "Remotive Demo Co",
        "Remote",
        ["python", "fastapi", "remote"],
        "https://remotive.com/remote-jobs/software-dev/demo-python-api",
    ),
    (
        "Frontend Engineer (React)",
        "RemoteCraft",
        "Remote",
        ["javascript", "react", "typescript"],
        "https://remotive.com/remote-jobs/software-dev/demo-react",
    ),
]


class RemotiveScraper(BaseScraper):
    """
    Remotive public jobs API.

    Docs: https://remotive.com/api
    Endpoint: https://remotive.com/api/remote-jobs
    """

    name = "remotive"
    API_URL = "https://remotive.com/api/remote-jobs"

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        if os.getenv("NERAJOB_REMOTIVE_OFFLINE", "").strip() in {"1", "true", "yes"}:
            return self._offline(query, limit)

        headers = {
            "User-Agent": user_agent(),
            "Accept": "application/json",
        }
        try:
            with httpx.Client(timeout=http_timeout(), headers=headers, follow_redirects=True) as client:
                response = client.get(self.API_URL)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return self._offline(query, limit)

        jobs_raw = payload.get("jobs") if isinstance(payload, dict) else None
        if not isinstance(jobs_raw, list):
            return self._offline(query, limit)

        q = query.strip().lower()
        jobs: list[JobPosting] = []
        for item in jobs_raw:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            company = str(item.get("company_name") or "").strip()
            if not title:
                continue
            tags = [str(t).lower() for t in (item.get("tags") or []) if t]
            category = str(item.get("category") or "")
            hay = f"{title} {company} {category} {' '.join(tags)} {item.get('description', '')}".lower()
            if q and q not in hay:
                continue
            loc = str(item.get("candidate_required_location") or "Remote")
            url = str(item.get("url") or "")
            raw_id = str(item.get("id") or title)
            digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]
            jobs.append(
                JobPosting(
                    id=f"remotive-{digest}",
                    source=self.name,
                    title=title,
                    company=company or "Unknown",
                    location=loc or "Remote",
                    url=url,
                    description=_strip_html(str(item.get("description") or ""))[:4000],
                    tags=tags[:20],
                    remote=True,
                    raw={"remotive_id": raw_id, "category": category},
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
                    id=f"remotive-{digest}",
                    source=self.name,
                    title=title,
                    company=company,
                    location=place,
                    url=url,
                    description=f"{title} at {company} (offline Remotive sample).",
                    tags=tags,
                    remote=True,
                    raw={"offline": True},
                )
            )
            if len(out) >= limit:
                break
        return out


def _strip_html(value: str) -> str:
    import re

    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", text).strip()
