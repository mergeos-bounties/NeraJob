"""
Jobicy scraper — remote jobs API.

Source: https://jobicy.com
Public JSON API — no auth required.
"""
from __future__ import annotations

import hashlib
import re

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper


class JobicyScraper(BaseScraper):
    """
    Jobicy public remote jobs API adapter.

    API: GET https://jobicy.com/api/v2/remote-jobs
    Params: tag (search keyword), count (results per page), page
    No auth required.

    ToS: free for personal/non-commercial use.
    """

    name = "jobicy"
    API_URL = "https://jobicy.com/api/v2/remote-jobs"

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
        page = 1

        try:
            with httpx.Client(timeout=http_timeout(), headers=headers, follow_redirects=True) as client:
                while len(jobs) < limit:
                    params: dict[str, int | str] = {
                        "count": min(limit, 50),
                        "page": page,
                    }
                    if query:
                        params["tag"] = query

                    resp = client.get(self.API_URL, params=params)
                    resp.raise_for_status()
                    payload = resp.json()

                    raw_jobs = payload.get("jobs") or []
                    if not raw_jobs:
                        break

                    for item in raw_jobs:
                        posting = self._parse(item)
                        if posting:
                            # Client-side filter
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

                    if len(raw_jobs) < 50:
                        break
                    page += 1

        except Exception:
            return []

        return jobs[:limit]

    def _parse(self, item: dict) -> JobPosting | None:
        title = str(item.get("jobTitle") or item.get("job_title") or "").strip()
        company = str(item.get("companyName") or item.get("company_name") or "Unknown").strip()
        if not title:
            return None

        url = str(item.get("url") or "")
        raw_id = str(item.get("id") or item.get("jobSlug") or title)

        digest = hashlib.sha1(f"{self.name}:{raw_id}:{company}".encode()).hexdigest()[:12]

        tags: list[str] = []
        for t in item.get("jobIndustry") or item.get("job_industry") or []:
            if t and t not in tags:
                tags.append(str(t).strip())
        for t in item.get("jobType") or item.get("job_type") or []:
            if t and t not in tags:
                tags.append(str(t).strip())
        job_level = item.get("jobLevel") or item.get("job_level") or ""
        if job_level and job_level not in tags:
            tags.append(str(job_level).strip())

        location_str = str(item.get("jobGeo") or item.get("job_geo") or "Remote Worldwide")

        excerpt = str(item.get("jobExcerpt") or item.get("job_excerpt") or "")
        description = _strip_html(excerpt)[:4000]

        return JobPosting(
            id=f"jobicy-{digest}",
            source=self.name,
            title=title,
            company=company,
            location=location_str,
            url=url,
            description=description,
            tags=tags[:20],
            salary="",
            remote=True,
            raw={"jobicy_id": raw_id, "job_level": job_level},
        )


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", text).strip()