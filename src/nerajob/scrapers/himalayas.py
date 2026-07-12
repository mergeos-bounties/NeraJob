"""
Himalayas scraper — remote-first job board.

Source: https://himalayas.app
Public JSON API at /jobs/api — no auth for basic search.
"""
from __future__ import annotations

import hashlib
import re

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper


class HimalayasScraper(BaseScraper):
    """
    Himalayas.app public jobs API adapter.

    API: GET https://himalayas.app/jobs/api
    Params: search, offset, limit
    No auth required for basic search.

    Returns salary metadata (min/max) and location restrictions.
    Rate-limit note: Polite usage. ToS: free for personal/non-commercial.
    """

    name = "himalayas"
    API_URL = "https://himalayas.app/jobs/api"

    def search(
        self,
        query: str = "",
        location: str = "",
        limit: int = 20,
    ) -> list[JobPosting]:
        headers = {
            "User-Agent": user_agent(),
            "Accept": "application/json",
        }

        q = query.strip().lower()
        jobs: list[JobPosting] = []
        offset = 0

        try:
            with httpx.Client(timeout=http_timeout(), headers=headers, follow_redirects=True) as client:
                while len(jobs) < limit:
                    params: dict[str, int | str] = {"limit": min(limit, 100)}
                    if query:
                        params["search"] = query
                    if location:
                        params["location"] = location
                    params["offset"] = offset

                    resp = client.get(self.API_URL, params=params)
                    resp.raise_for_status()
                    payload = resp.json()

                    raw_jobs = payload.get("jobs") or []
                    if not raw_jobs:
                        break

                    for item in raw_jobs:
                        posting = self._parse(item)
                        if posting:
                            # Client-side filter (robust regardless of API search quality)
                            hay = (
                                posting.title.lower()
                                + " "
                                + posting.company.lower()
                                + " "
                                + " ".join(posting.tags)
                            )
                            if q and q not in hay:
                                continue
                            jobs.append(posting)
                        if len(jobs) >= limit:
                            break

                    if len(raw_jobs) < 100:
                        break

                    offset += len(raw_jobs)

        except Exception:
            return []

        return jobs[:limit]

    def _parse(self, item: dict) -> JobPosting | None:
        title = str(item.get("title") or "").strip()
        company = str(item.get("companyName") or item.get("company_name") or "Unknown").strip()
        if not title:
            return None

        url = str(item.get("link") or item.get("url") or "")
        slug = str(item.get("slug") or title)
        raw_id = str(item.get("id") or slug)

        # Stable id
        digest = hashlib.sha1(f"{self.name}:{raw_id}:{company}".encode()).hexdigest()[:12]

        tags: list[str] = []
        for t in (item.get("categories") or []):
            tag = str(t).replace("-", " ").replace("_", " ").strip()
            if tag and tag not in tags:
                tags.append(tag)
        for t in (item.get("parentCategories") or []):
            tag = str(t).strip()
            if tag and tag not in tags:
                tags.append(tag)
        for t in (item.get("seniority") or []):
            tag = str(t).strip()
            if tag and tag not in tags:
                tags.append(tag)

        employment_type = str(item.get("employmentType") or item.get("employment_type") or "")
        normalized = self._normalise_employment_type(employment_type)
        if normalized and normalized not in tags:
            tags.append(normalized)

        location_restrictions = item.get("locationRestrictions") or []
        if location_restrictions:
            location_str = ", ".join(str(loc) for loc in location_restrictions)
            remote = False
        else:
            location_str = "Remote Worldwide"
            remote = True

        min_salary = item.get("minSalary") or item.get("min_salary")
        max_salary = item.get("maxSalary") or item.get("max_salary")
        salary_period = str(item.get("salaryPeriod") or "annual")
        salary = self._format_salary(min_salary, max_salary, salary_period)

        excerpt = str(item.get("excerpt") or item.get("description") or "")[:4000]
        description = _strip_html(excerpt)[:4000]

        return JobPosting(
            id=f"himalayas-{digest}",
            source=self.name,
            title=title,
            company=company,
            location=location_str,
            url=url,
            description=description,
            tags=tags[:20],
            salary=salary,
            remote=remote,
            raw={
                "himalayas_id": raw_id,
                "employment_type": employment_type,
                "min_salary": min_salary,
                "max_salary": max_salary,
            },
        )

    @staticmethod
    def _normalise_employment_type(raw: str) -> str:
        mapping = {
            "full time": "Full-time",
            "fulltime": "Full-time",
            "part time": "Part-time",
            "parttime": "Part-time",
            "contract": "Contract",
            "contractor": "Contract",
            "freelance": "Freelance",
            "internship": "Internship",
            "temporary": "Temporary",
        }
        lower = raw.strip().lower().replace(" ", "")
        return mapping.get(lower, raw.strip())

    @staticmethod
    def _format_salary(min_sal, max_sal, period: str) -> str:
        if not min_sal and not max_sal:
            return ""
        p = "/yr" if "annual" in period else f"/{period}"
        if min_sal and max_sal:
            return f"${min_sal:,.0f} – ${max_sal:,.0f}{p}"
        elif max_sal:
            return f"Up to ${max_sal:,.0f}{p}"
        elif min_sal:
            return f"From ${min_sal:,.0f}{p}"
        return ""


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", text).strip()