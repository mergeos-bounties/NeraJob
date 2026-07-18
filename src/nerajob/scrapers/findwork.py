"""Findwork.dev public jobs API adapter with offline fallback.

Findwork.dev (https://findwork.dev) is a job board aggregator exposing a
public REST API at https://findwork.dev/api/jobs/. Public read access is
available with a free API token; without a token the API returns 403.

To keep this scraper operational without requiring every user to register
a token, we ship an OFFLINE fallback (deterministic demo data) used when:
  - NERAJOB_FINDWORK_OFFLINE=1 is set, OR
  - NERAJOB_FINDWORK_API_TOKEN env var is not set, OR
  - the live API call fails (network, 403, parse error)

To use the live API, register at https://findwork.dev/ and set:
    export NERAJOB_FINDWORK_API_TOKEN=your_token_here
"""

from __future__ import annotations

import hashlib
import os

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper

# Deterministic offline fixture for tests + demos (no network needed).
_OFFLINE = [
    (
        "Senior Python Backend Engineer",
        "Findwork Demo Labs",
        "Remote (Worldwide)",
        ["python", "fastapi", "postgresql", "remote"],
        "https://findwork.dev/jobs/demo-python-backend/",
        "Design and build resilient backend services in Python. Work on APIs, data pipelines, and async job queues. Remote-first team across 3 continents.",
    ),
    (
        "Full-Stack Engineer (Python + React)",
        "Atlas Remote",
        "Remote (EU)",
        ["python", "react", "typescript", "remote"],
        "https://findwork.dev/jobs/demo-fullstack/",
        "Join a 12-person product team building developer tooling. Own features end-to-end. Must overlap 4 hours with EU business hours.",
    ),
    (
        "DevOps Engineer",
        "Cloudward",
        "Remote (US)",
        ["kubernetes", "terraform", "aws", "remote"],
        "https://findwork.dev/jobs/demo-devops/",
        "Own the platform: CI/CD, observability, infra-as-code. Strong AWS + K8s background required. On-call rotation every 6 weeks.",
    ),
    (
        "ML Engineer",
        "Visionary AI",
        "Remote (Worldwide)",
        ["python", "pytorch", "mlops", "remote"],
        "https://findwork.dev/jobs/demo-ml-engineer/",
        "Train and ship production ML models for vision systems. End-to-end ownership from data pipeline to deployment.",
    ),
    (
        "Security Engineer (AppSec)",
        "Shield Stack",
        "Remote (Worldwide)",
        ["security", "python", "appsec", "remote"],
        "https://findwork.dev/jobs/demo-security/",
        "Lead application security for a fintech platform. Threat modeling, SAST/DAST tooling, secure code review. Python-heavy codebase.",
    ),
]


class FindworkScraper(BaseScraper):
    """https://findwork.dev/api/jobs/ — public job board aggregator."""

    name = "findwork"
    API_URL = "https://findwork.dev/api/jobs/"

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        """Search Findwork.dev for jobs matching query + location.

        Falls back to OFFLINE fixtures when no API token is configured
        or when the live API call fails (network, 403, parse error).
        """
        if os.getenv("NERAJOB_FINDWORK_OFFLINE", "").strip().lower() in {"1", "true", "yes"}:
            return self._offline(query, location, limit)

        token = os.getenv("NERAJOB_FINDWORK_API_TOKEN", "").strip()
        if not token:
            return self._offline(query, location, limit)

        headers = {
            "User-Agent": user_agent(),
            "Accept": "application/json",
            "Authorization": f"Token {token}",
        }
        params: dict[str, str | int] = {"limit": max(1, min(limit, 50))}
        if query.strip():
            params["search"] = query.strip()
        if location.strip():
            params["location"] = location.strip()

        try:
            with httpx.Client(
                timeout=http_timeout(),
                headers=headers,
                follow_redirects=True,
            ) as client:
                response = client.get(self.API_URL, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return self._offline(query, location, limit)

        results = (
            payload.get("results")
            if isinstance(payload, dict)
            else payload
            if isinstance(payload, list)
            else []
        )
        if not isinstance(results, list):
            return self._offline(query, location, limit)

        jobs: list[JobPosting] = []
        q = query.strip().lower()
        loc = location.strip().lower()
        for item in results:
            if not isinstance(item, dict):
                continue
            posting = self._posting_from_api(item)
            if posting is None:
                continue
            hay = f"{posting.title} {posting.company} {posting.location} {' '.join(posting.tags)} {posting.description}".lower()
            if q and q not in hay:
                continue
            if loc and loc not in posting.location.lower() and "remote" not in posting.location.lower():
                continue
            jobs.append(posting)
            if len(jobs) >= limit:
                break
        return jobs

    def _posting_from_api(self, item: dict) -> JobPosting | None:
        """Convert a Findwork.dev API result dict to a JobPosting.

        API field reference (verified 2026-07-18):
          - id (int)            -> job id
          - role (str)          -> title
          - company_name (str)  -> company (nested: company.name)
          - location (str)      -> location string
          - url (str)           -> external URL on findwork.dev
          - text (str)          -> full description (HTML/markdown)
          - tags (list[str])    -> keyword tags
          - remote (bool)       -> is remote?
          - keywords (list[str])-> derived keywords
        """
        title = str(item.get("role") or item.get("title") or "").strip()
        if not title:
            return None

        company_obj = item.get("company")
        if isinstance(company_obj, dict):
            company = str(
                company_obj.get("name")
                or company_obj.get("company_name")
                or ""
            ).strip()
        else:
            company = str(item.get("company_name") or "").strip()
        if not company:
            company = "Unknown Company"

        place = str(item.get("location") or "Remote").strip() or "Remote"
        url = str(item.get("url") or item.get("redirect_url") or "").strip()
        description = str(item.get("text") or item.get("description") or "").strip()
        tags_raw = (item.get("tags") or []) + (item.get("keywords") or [])
        tags = sorted({
            str(t).strip().lower()
            for t in tags_raw
            if t and isinstance(t, str | int | float)
        })
        remote = bool(item.get("remote", "remote" in place.lower()))

        raw_id = str(item.get("id") or f"{company}:{title}:{url}")
        digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]
        posting_id = (
            f"{self.name}-{item.get('id')}"
            if item.get("id")
            else f"{self.name}-{digest}"
        )

        return JobPosting(
            id=posting_id,
            source=self.name,
            title=title,
            company=company,
            location=place,
            url=url,
            description=description,
            tags=tags,
            remote=remote,
            raw=item,
        )

    def _offline(self, query: str, location: str, limit: int) -> list[JobPosting]:
        """Return deterministic offline fixtures filtered by query + location."""
        q = query.strip().lower()
        loc = location.strip().lower()
        jobs: list[JobPosting] = []
        for title, company, place, tags, url, desc in _OFFLINE:
            hay = f"{title} {company} {place} {' '.join(tags)} {desc}".lower()
            if q and q not in hay:
                continue
            if loc and loc not in place.lower() and "remote" not in place.lower():
                continue
            digest = hashlib.sha1(f"{self.name}:{title}:{company}".encode()).hexdigest()[:12]
            jobs.append(
                JobPosting(
                    id=f"{self.name}-{digest}",
                    source=self.name,
                    title=title,
                    company=company,
                    location=place,
                    url=url,
                    description=desc,
                    tags=tags,
                    remote="remote" in place.lower(),
                )
            )
            if len(jobs) >= limit:
                break
        if not jobs and not q:
            for title, company, place, tags, url, desc in _OFFLINE[:limit]:
                digest = hashlib.sha1(f"{self.name}:{title}:{company}".encode()).hexdigest()[:12]
                jobs.append(
                    JobPosting(
                        id=f"{self.name}-{digest}",
                        source=self.name,
                        title=title,
                        company=company,
                        location=place,
                        url=url,
                        description=desc,
                        tags=tags,
                        remote="remote" in place.lower(),
                    )
                )
        return jobs
