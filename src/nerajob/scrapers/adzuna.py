"""Adzuna Jobs API adapter with offline fallback.

Adzuna (https://adzuna.com) provides a RESTful job search API across
multiple countries.  A free API key (app_id + app_key) is required for
live calls; register at https://developer.adzuna.com/signup.

Behaviour:
  - When NERAJOB_ADZUNA_OFFLINE=1 is set, or the env credentials are
    missing, or the live call fails → deterministic offline fixtures.
  - When ADZUNA_APP_ID and ADZUNA_APP_KEY are both set → live API.
  - Country defaults to ``gb``; can be override with ``--country`` CLI
    arg or by setting ``NERAJOB_ADZUNA_COUNTRY`` env var.

API docs: https://developer.adzuna.com/overview
Rate limit: free tier is 50 calls / day (use responsibly).

Bounty: https://github.com/mergeos-bounties/NeraJob/issues/7 (50 MRG)
"""

from __future__ import annotations

import hashlib
import os

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper

# ── deterministic offline fixtures ──────────────────────────────────────

_OFFLINE: list[tuple[str, str, str, list[str], str, str]] = [
    (
        "Python Developer",
        "Adzuna Demo Ltd",
        "London, UK",
        ["python", "django", "postgresql"],
        "https://adzuna.com/jobs/demo-python-dev",
        "Backend Python developer with Django experience. Hybrid London.",
    ),
    (
        "Frontend Engineer",
        "Adzuna Demo Ltd",
        "Remote UK",
        ["javascript", "react", "typescript", "css"],
        "https://adzuna.com/jobs/demo-frontend",
        "Frontend engineer for product team. Remote-first within UK timezone.",
    ),
    (
        "DevOps Engineer",
        "Cloud Native Inc",
        "Berlin, Germany",
        ["kubernetes", "terraform", "aws", "ci-cd"],
        "https://adzuna.com/jobs/demo-devops",
        "Platform engineering role. K8s + Terraform + AWS. On-call rotation.",
    ),
    (
        "Data Scientist",
        "DataDriven Co",
        "Remote (EU)",
        ["python", "machine-learning", "tensorflow", "sql"],
        "https://adzuna.com/jobs/demo-data-scientist",
        "Build and deploy ML models. Remote-first EU team.",
    ),
]


class AdzunaScraper(BaseScraper):
    """https://api.adzuna.com/v1/api/jobs — Multi-country job search API."""

    name = "adzuna"
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def search(
        self,
        query: str = "",
        location: str = "",
        limit: int = 20,
    ) -> list[JobPosting]:
        """Search Adzuna for jobs matching *query* and *location*.

        Parameters
        ----------
        query : str
            Free-text search (job title, skill, keyword).
        location : str
            Where string (e.g. ``"London"``).  Used as-is; Adzuna does its
            own geo-resolution when ``where`` is passed.
        limit : int
            Max results to return (capped at API page size 50).

        Returns
        -------
        list[JobPosting]
            Matched job postings, or offline fixtures on failure.
        """
        if os.getenv("NERAJOB_ADZUNA_OFFLINE", "").strip().lower() in {"1", "true", "yes"}:
            return self._offline(query, location, limit)

        app_id = os.getenv("ADZUNA_APP_ID", "").strip()
        app_key = os.getenv("ADZUNA_APP_KEY", "").strip()
        if not app_id or not app_key:
            return self._offline(query, location, limit)

        country = (
            os.getenv("NERAJOB_ADZUNA_COUNTRY", "").strip()
            or location.split(",")[-1].strip().lower()
            or "gb"
        )
        # Normalise common country names to 2-letter codes
        country_map = {
            "uk": "gb", "united kingdom": "gb", "great britain": "gb",
            "us": "us", "usa": "us", "united states": "us",
            "de": "de", "germany": "de",
            "au": "au", "australia": "au",
            "ca": "ca", "canada": "ca",
            "in": "in", "india": "in",
            "fr": "fr", "france": "fr",
            "nl": "nl", "netherlands": "nl",
            "br": "br", "brazil": "br",
            "nz": "nz", "new zealand": "nz",
            "za": "za", "south africa": "za",
            "sg": "sg", "singapore": "sg",
            "ae": "ae", "united arab emirates": "ae",
        }
        country = country_map.get(country, country)

        params: dict[str, str | int] = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": max(1, min(limit, 50)),
        }
        if query.strip():
            params["what"] = query.strip()
        if location.strip():
            # Use the full location string as "where" param
            params["where"] = location.strip()

        url = f"{self.BASE_URL}/{country}/search/1"
        headers = {
            "User-Agent": user_agent(),
            "Accept": "application/json",
        }

        try:
            with httpx.Client(
                timeout=http_timeout(),
                headers=headers,
                follow_redirects=True,
            ) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return self._offline(query, location, limit)

        results = payload.get("results") if isinstance(payload, dict) else []
        if not isinstance(results, list):
            return self._offline(query, location, limit)

        q = query.strip().lower()
        loc = location.strip().lower()
        jobs: list[JobPosting] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            posting = self._posting_from_api(item, country)
            if posting is None:
                continue
            hay = (
                f"{posting.title} {posting.company} {posting.location} "
                f"{' '.join(posting.tags)} {posting.description}"
            ).lower()
            if q and q not in hay:
                continue
            if loc and loc not in posting.location.lower() and "remote" not in posting.location.lower():
                continue
            jobs.append(posting)
            if len(jobs) >= limit:
                break

        return jobs if jobs else self._offline(query, location, limit)

    # ── helpers ─────────────────────────────────────────────────────────

    def _posting_from_api(self, item: dict, country: str) -> JobPosting | None:
        """Convert an Adzuna API result dict to a JobPosting.

        Adzuna API field reference:
          - id (str)            -> job ad id
          - title (str)         -> job title
          - company.display_name (str)  -> company name
          - location.display_name (str) -> location string
          - redirect_url (str)  -> URL on adzuna.com
          - description (str)   -> full description (HTML)
          - category.label (str) -> job category
          - contract_type (str) -> "permanent", "contract", etc.
          - salary_min (float)  -> minimum salary
          - salary_max (float)  -> maximum salary
          - salary_is_predicted (str) -> "1" if estimated
        """
        title = str(item.get("title") or "").strip()
        if not title:
            return None

        company_obj = item.get("company") or {}
        company = (
            str(company_obj.get("display_name") or "")
            if isinstance(company_obj, dict)
            else str(item.get("company_name") or "")
        ).strip()
        if not company:
            company = "Unknown Company"

        loc_obj = item.get("location") or {}
        place = (
            str(loc_obj.get("display_name") or "")
            if isinstance(loc_obj, dict)
            else str(item.get("location") or "Remote")
        ).strip()
        if not place:
            place = "Remote"

        url = str(item.get("redirect_url") or item.get("url") or "").strip()
        description = str(item.get("description") or "").strip()[:4000]
        salary_min = item.get("salary_min")
        salary_max = item.get("salary_max")
        salary_str = ""
        if salary_min is not None or salary_max is not None:
            low = f"£{salary_min:,.0f}" if salary_min else ""
            high = f"£{salary_max:,.0f}" if salary_max else ""
            salary_str = f"{low}–{high}" if low and high else (low or high)

        tags: list[str] = []
        cat = item.get("category")
        if isinstance(cat, dict):
            label = str(cat.get("label") or "").strip().lower()
            if label:
                tags.append(label)
        ctype = str(item.get("contract_type") or "").strip().lower()
        if ctype:
            tags.append(ctype)

        raw_id = str(item.get("id") or f"{company}:{title}")
        digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]

        return JobPosting(
            id=f"{self.name}-{digest}",
            source=self.name,
            title=title,
            company=company,
            location=place,
            url=url,
            description=description,
            tags=tags[:20],
            salary=salary_str,
            remote="remote" in place.lower(),
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
                    tags=tags[:20],
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
                        tags=tags[:20],
                        remote="remote" in place.lower(),
                    )
                )
        return jobs
