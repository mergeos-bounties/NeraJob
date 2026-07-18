"""Greenhouse public job board API adapter with offline fallback."""

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
        "Software Engineer",
        "Greenhouse Demo Inc",
        "San Francisco, CA / Remote",
        ["python", "backend", "api"],
        "https://boards.greenhouse.io/greenhousedemo/jobs/1",
    ),
    (
        "Product Designer",
        "DesignBoard Co",
        "New York, NY",
        ["design", "ux", "figma"],
        "https://boards.greenhouse.io/greenhousedemo/jobs/2",
    ),
    (
        "Data Scientist",
        "DataGreen Labs",
        "Remote",
        ["python", "machine learning", "sql", "statistics"],
        "https://boards.greenhouse.io/greenhousedemo/jobs/3",
    ),
]


class GreenhouseScraper(BaseScraper):
    """
    Greenhouse public job board API.

    Docs: https://developers.greenhouse.io/job-board.html
    Endpoint: https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs
    Set NERAJOB_GREENHOUSE_BOARD to a company board token (e.g. `acme`).
    Without env, uses offline sample postings.
    """

    name = "greenhouse"
    API_BASE = "https://boards-api.greenhouse.io/v1/boards"

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        board = os.getenv("NERAJOB_GREENHOUSE_BOARD", "").strip()
        if not board:
            return self._offline(query, limit)

        headers = {"User-Agent": user_agent(), "Accept": "application/json"}
        params = {"content": "true"}
        url = f"{self.API_BASE}/{board}/jobs"

        try:
            with httpx.Client(timeout=http_timeout(), headers=headers, follow_redirects=True) as client:
                response = client.get(url, params=params)
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
            if not title:
                continue
            location_obj = item.get("location")
            if isinstance(location_obj, dict):
                place = str(location_obj.get("name") or "Remote")
            else:
                place = "Remote"
            company = ""
            departments = item.get("departments") or []
            if isinstance(departments, list):
                dept_names = [d.get("name", "") for d in departments if isinstance(d, dict)]
                company = dept_names[0] if dept_names else "Greenhouse"
            offices = item.get("offices") or []
            if isinstance(offices, list) and not company:
                office_names = [o.get("name", "") for o in offices if isinstance(o, dict)]
                company = office_names[0] if office_names else "Greenhouse"

            content = str(item.get("content") or "")
            description = _strip_html(content)
            url = str(item.get("absolute_url") or "")
            raw_id = str(item.get("id") or title)
            digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]

            hay = f"{title} {company} {place} {description}".lower()
            if q and q not in hay:
                continue

            tags = []
            if departments:
                for d in departments:
                    if isinstance(d, dict) and d.get("name"):
                        tags.append(str(d["name"]).lower())
            if offices:
                for o in offices:
                    if isinstance(o, dict) and o.get("name"):
                        tags.append(str(o["name"]).lower())

            jobs.append(
                JobPosting(
                    id=f"greenhouse-{digest}",
                    source=self.name,
                    title=title,
                    company=company or "Unknown",
                    location=place,
                    url=url,
                    description=description[:4000],
                    tags=tags[:20],
                    remote="remote" in place.lower(),
                    raw={"greenhouse_id": raw_id, "board": board},
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
                    id=f"greenhouse-{digest}",
                    source=self.name,
                    title=title,
                    company=company,
                    location=place,
                    url=url,
                    description=f"{title} at {company} (offline Greenhouse sample).",
                    tags=tags,
                    remote="remote" in place.lower(),
                    raw={"offline": True},
                )
            )
            if len(out) >= limit:
                break
        return out


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", text).strip()
