"""Jobicy public remote jobs API adapter with offline fallback."""

from __future__ import annotations

import hashlib
import os
import re

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper

_OFFLINE = [
    (
        "Python Backend Engineer",
        "Jobicy Demo Labs",
        "Remote",
        ["python", "backend", "api"],
        "https://jobicy.com/jobs/demo-python-backend",
    ),
    (
        "DevOps Engineer",
        "RemoteOps Co",
        "Europe",
        ["devops", "kubernetes", "aws"],
        "https://jobicy.com/jobs/demo-devops-engineer",
    ),
    (
        "Frontend Engineer",
        "UICraft",
        "Worldwide",
        ["react", "typescript", "frontend"],
        "https://jobicy.com/jobs/demo-frontend-engineer",
    ),
]


class JobicyScraper(BaseScraper):
    """
    Jobicy public remote jobs API.

    Docs: https://jobicy.com/jobs-rss-feed
    Endpoint: https://jobicy.com/api/v2/remote-jobs
    """

    name = "jobicy"
    API_URL = "https://jobicy.com/api/v2/remote-jobs"

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        if os.getenv("NERAJOB_JOBICY_OFFLINE", "").strip().lower() in {"1", "true", "yes"}:
            return self._offline(query, limit)

        headers = {"User-Agent": user_agent(), "Accept": "application/json"}
        params: dict[str, str | int] = {"count": limit}
        q = query.strip()
        loc = location.strip()
        if q:
            params["tag"] = q
        if loc:
            params["geo"] = loc.lower()

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

        query_lc = q.lower()
        loc_lc = loc.lower()
        jobs: list[JobPosting] = []
        for item in jobs_raw:
            if not isinstance(item, dict):
                continue
            title = str(item.get("jobTitle") or "").strip()
            company = str(item.get("companyName") or "").strip()
            if not title:
                continue

            tags = _string_list(item.get("jobIndustry")) + _string_list(item.get("jobType"))
            level = str(item.get("jobLevel") or "").strip()
            if level:
                tags.append(level.lower())
            place = str(item.get("jobGeo") or "Remote").strip() or "Remote"
            description = _strip_html(str(item.get("jobDescription") or item.get("jobExcerpt") or ""))
            hay = f"{title} {company} {place} {' '.join(tags)} {description}".lower()
            if query_lc and query_lc not in hay:
                continue
            if loc_lc and loc_lc not in place.lower() and place.lower() != "remote":
                continue

            raw_id = str(item.get("id") or item.get("jobSlug") or item.get("url") or title)
            digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]
            salary = _salary(item)
            jobs.append(
                JobPosting(
                    id=f"jobicy-{digest}",
                    source=self.name,
                    title=title,
                    company=company or "Unknown",
                    location=place,
                    url=str(item.get("url") or ""),
                    description=description[:4000],
                    tags=tags[:20],
                    salary=salary,
                    remote=True,
                    raw={"jobicy_id": raw_id, "job_slug": item.get("jobSlug")},
                )
            )
            if len(jobs) >= limit:
                break
        return jobs if jobs else self._offline(query, limit)

    def _offline(self, query: str, limit: int) -> list[JobPosting]:
        q = query.strip().lower()
        out: list[JobPosting] = []
        for title, company, place, tags, url in _OFFLINE:
            hay = f"{title} {company} {place} {' '.join(tags)}".lower()
            if q and q not in hay:
                continue
            digest = hashlib.sha1(f"{self.name}:{title}:{company}".encode()).hexdigest()[:12]
            out.append(
                JobPosting(
                    id=f"jobicy-{digest}",
                    source=self.name,
                    title=title,
                    company=company,
                    location=place,
                    url=url,
                    description=f"{title} at {company} (offline Jobicy sample).",
                    tags=tags,
                    remote=True,
                    raw={"offline": True},
                )
            )
            if len(out) >= limit:
                break
        return out


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip().lower() for item in value if str(item).strip()]
    if value:
        return [str(value).strip().lower()]
    return []


def _salary(item: dict[str, object]) -> str:
    minimum = str(item.get("annualSalaryMin") or "").strip()
    maximum = str(item.get("annualSalaryMax") or "").strip()
    currency = str(item.get("salaryCurrency") or "").strip()
    if minimum and maximum:
        return f"{minimum}-{maximum} {currency}".strip()
    if minimum:
        return f"{minimum}+ {currency}".strip()
    if maximum:
        return f"up to {maximum} {currency}".strip()
    return ""


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", text).strip()
