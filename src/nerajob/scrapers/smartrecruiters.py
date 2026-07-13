"""SmartRecruiters public postings API adapter with offline fallback."""

from __future__ import annotations

import hashlib
import os

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper

_OFFLINE = [
    (
        "Senior Python Engineer",
        "SmartRecruiters Demo",
        "Berlin, Germany / Remote",
        ["python", "backend", "api"],
        "https://jobs.smartrecruiters.com/demo/senior-python-engineer",
        "Build Python APIs for a public postings platform.",
    ),
    (
        "Platform Engineer",
        "Hiring Cloud",
        "Remote",
        ["platform", "kubernetes", "python"],
        "https://jobs.smartrecruiters.com/demo/platform-engineer",
        "Operate platform services and automation.",
    ),
    (
        "Frontend Engineer",
        "Talent UI",
        "Paris, France",
        ["frontend", "typescript", "react"],
        "https://jobs.smartrecruiters.com/demo/frontend-engineer",
        "Build candidate-facing application flows.",
    ),
]


class SmartRecruitersScraper(BaseScraper):
    """https://developers.smartrecruiters.com/docs/postings-api"""

    name = "smartrecruiters"
    API_URL = "https://api.smartrecruiters.com/v1/companies"

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        if os.getenv("NERAJOB_SMARTRECRUITERS_OFFLINE", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }:
            return self._offline(query, limit)

        companies = _configured_companies()
        if not companies:
            return self._offline(query, limit)

        q = query.strip()
        loc = location.strip()
        params: dict[str, str | int] = {
            "q": q,
            "limit": min(max(limit, 1), 100),
            "offset": 0,
        }
        if loc:
            params["location"] = loc

        headers = {"User-Agent": user_agent(), "Accept": "application/json"}
        jobs: list[JobPosting] = []
        try:
            with httpx.Client(
                timeout=http_timeout(), headers=headers, follow_redirects=True
            ) as client:
                for company_id in companies:
                    response = client.get(f"{self.API_URL}/{company_id}/postings", params=params)
                    response.raise_for_status()
                    payload = response.json()
                    jobs.extend(self._parse_payload(payload, q, loc, limit - len(jobs)))
                    if len(jobs) >= limit:
                        break
        except Exception:
            return self._offline(query, limit)

        return jobs

    def _parse_payload(
        self, payload: object, query: str, location: str, limit: int
    ) -> list[JobPosting]:
        items = payload.get("content") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return []

        query_lc = query.lower()
        loc_lc = location.lower()
        jobs: list[JobPosting] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            title = str(item.get("name") or item.get("title") or "").strip()
            if not title:
                continue
            company = _company_name(item.get("company"))
            place = _location(item.get("location"))
            tags = _tags(item.get("department"))
            description = _description(item.get("jobAd"))
            hay = f"{title} {company} {place} {' '.join(tags)} {description}".lower()
            if query_lc and query_lc not in hay:
                continue
            if loc_lc and loc_lc not in place.lower():
                continue

            raw_id = str(item.get("id") or item.get("ref") or item.get("postingUrl") or title)
            digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]
            jobs.append(
                JobPosting(
                    id=f"smartrecruiters-{digest}",
                    source=self.name,
                    title=title,
                    company=company or "Unknown",
                    location=place or "Remote",
                    url=str(
                        item.get("postingUrl") or item.get("applyUrl") or item.get("url") or ""
                    ),
                    description=description[:4000],
                    tags=tags[:20],
                    remote="remote" in place.lower(),
                    raw={"smartrecruiters_id": raw_id},
                )
            )
            if len(jobs) >= limit:
                break
        return jobs

    def _offline(self, query: str, limit: int) -> list[JobPosting]:
        q = query.strip().lower()
        out: list[JobPosting] = []
        for title, company, place, tags, url, description in _OFFLINE:
            hay = f"{title} {company} {place} {' '.join(tags)} {description}".lower()
            if q and q not in hay:
                continue
            digest = hashlib.sha1(f"{self.name}:{title}:{company}".encode()).hexdigest()[:12]
            out.append(
                JobPosting(
                    id=f"smartrecruiters-{digest}",
                    source=self.name,
                    title=title,
                    company=company,
                    location=place,
                    url=url,
                    description=description,
                    tags=tags,
                    remote="remote" in place.lower(),
                    raw={"offline": True},
                )
            )
            if len(out) >= limit:
                break
        return out


def _company_name(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or "").strip()
    return str(value or "").strip()


def _configured_companies() -> list[str]:
    raw = os.getenv("NERAJOB_SMARTRECRUITERS_COMPANIES", "")
    return [part.strip() for part in raw.split(",") if part.strip()]


def _location(value: object) -> str:
    if isinstance(value, dict):
        city = str(value.get("city") or "").strip()
        country = str(value.get("country") or "").strip()
        if city and country:
            return f"{city}, {country}"
        return city or country
    return str(value or "Remote").strip() or "Remote"


def _tags(value: object) -> list[str]:
    if isinstance(value, dict):
        label = str(value.get("label") or value.get("name") or "").strip().lower()
        return [label] if label else []
    if isinstance(value, list):
        return [str(item).strip().lower() for item in value if str(item).strip()]
    if value:
        return [str(value).strip().lower()]
    return []


def _description(value: object) -> str:
    if isinstance(value, dict):
        sections = value.get("sections")
        if isinstance(sections, dict):
            chunks = []
            for section in sections.values():
                if isinstance(section, dict):
                    text = str(section.get("text") or "").strip()
                    if text:
                        chunks.append(text)
            return " ".join(chunks)
        return str(value.get("text") or value.get("description") or "").strip()
    return str(value or "").strip()
