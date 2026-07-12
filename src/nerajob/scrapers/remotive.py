"""
Remotive scraper — remote job board API.

Source: https://remotive.com/api
Public JSON API — no auth required for basic search.
"""
from __future__ import annotations

import hashlib
import re
from typing import Optional

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper


class RemotiveScraper(BaseScraper):
    """
    Remotive public jobs API adapter.

    API: GET https://remotive.com/api/remote-jobs
    Params: search, category, limit, offset
    No auth required for basic public search.

    Rate-limit note: Polite usage; add delay between requests if paginating.
    ToS: Free for personal/non-commercial use.
    """

    name = "remotive"
    API_URL = "https://remotive.com/api/remote-jobs"

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
                            # Client-side filter (API search can be loose)
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
        company = str(item.get("company_name") or "Unknown").strip()
        if not title:
            return None

        url = str(item.get("url") or "")
        raw_id = str(item.get("id") or title)

        # Stable id from id + company
        digest = hashlib.sha1(f"{self.name}:{raw_id}:{company}".encode()).hexdigest()[:12]

        tags_raw = item.get("tags") or []
        tags = [str(t).strip() for t in tags_raw if t][:20]

        job_type_raw = str(item.get("job_type") or "")
        # Normalise: full_time → Full-time, contract → Contract
        job_type = self._normalise_job_type(job_type_raw)
        if job_type and job_type not in tags:
            tags.append(job_type)

        location_str = str(item.get("candidate_required_location") or "Remote Worldwide")

        salary_raw = item.get("salary") or ""
        salary = str(salary_raw) if salary_raw else ""

        description = _strip_html(str(item.get("description") or ""))

        # Remotive is a remote-only board — all listings are remote jobs by definition
        remote = True

        return JobPosting(
            id=f"remotive-{digest}",
            source=self.name,
            title=title,
            company=company,
            location=location_str,
            url=url,
            description=description[:4000],
            tags=tags,
            salary=salary,
            remote=remote,
            raw={"remotive_id": raw_id, "job_type": job_type_raw},
        )

    @staticmethod
    def _normalise_job_type(raw: str) -> str:
        mapping = {
            "full_time": "Full-time",
            "contract": "Contract",
            "part_time": "Part-time",
            "freelance": "Freelance",
            "internship": "Internship",
            "temporary": "Temporary",
        }
        return mapping.get(raw.strip().lower(), raw.strip())


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", text).strip()