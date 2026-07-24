"""USAJOBS official API adapter with offline fallback.

USAJOBS (https://www.usajobs.gov) is the official job board of the
United States federal government, operated by the Office of Personnel
Management (OPM).  It exposes a free REST API:

  GET https://data.usajobs.gov/api/Search

An API key (free) is required for live calls; register at:
  https://developer.usajobs.gov/

Required headers for live API:
  - Host: data.usajobs.gov
  - Authorization-Key: {your_api_key}
  - User-Agent: {your_registered_email}

Behaviour:
  - When NERAJOB_USAJOBS_OFFLINE=1 is set, or NERAJOB_USAJOBS_API_KEY
    env var is missing, or the live call fails 鈫?deterministic offline
    fixtures.
  - When NERAJOB_USAJOBS_API_KEY is set 鈫?live API.

API docs: https://developer.usajobs.gov/api-reference/get-api-search
Rate limit: 1000 requests/day (free tier; use responsibly).

Bounty: https://github.com/mergeos-bounties/NeraJob/issues/8 (50 MRG)
"""

from __future__ import annotations

import hashlib
import os

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper

# 鈹€鈹€ deterministic offline fixtures 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

_OFFLINE: list[tuple[str, str, str, list[str], str, str, str]] = [
    (
        "IT Specialist (Infosec)",
        "Department of Homeland Security",
        "Washington DC, United States",
        ["information-technology", "cybersecurity", "full-time"],
        "https://www.usajobs.gov/GetJob/ViewDetails/99999901",
        "$92,108鈥?119,746",
        "Lead cybersecurity operations for DHS network defense. GS-13/14 equivalent.",
    ),
    (
        "Registered Nurse",
        "Department of Veterans Affairs",
        "San Francisco CA, United States",
        ["healthcare", "nursing", "full-time"],
        "https://www.usajobs.gov/GetJob/ViewDetails/99999902",
        "$75,000鈥?105,000",
        "Provide direct patient care at VA Medical Center. Multiple shifts available.",
    ),
    (
        "Civil Engineer",
        "US Army Corps of Engineers",
        "Portland OR, United States",
        ["engineering", "civil-engineering", "full-time"],
        "https://www.usajobs.gov/GetJob/ViewDetails/99999903",
        "$86,000鈥?112,000",
        "Design and oversee infrastructure projects for USACE Northwestern Division.",
    ),
    (
        "Data Scientist",
        "Bureau of Labor Statistics",
        "Washington DC, United States",
        ["data-science", "statistics", "python", "full-time"],
        "https://www.usajobs.gov/GetJob/ViewDetails/99999904",
        "$100,000鈥?140,000",
        "Apply statistical modeling and machine learning to federal economic indicators.",
    ),
]


class USAJobsScraper(BaseScraper):
    """https://data.usajobs.gov/api/Search 鈥?US federal job search API."""

    name = "usajobs"
    API_URL = "https://data.usajobs.gov/api/Search"

    def search(
        self,
        query: str = "",
        location: str = "",
        limit: int = 20,
    ) -> list[JobPosting]:
        """Search USAJOBS for federal job listings.

        Parameters
        ----------
        query : str
            Free-text keyword search (searches title + description).
        location : str
            City / state filter (e.g. ``"Washington DC"``).
        limit : int
            Max results to return (capped at 500 per API).

        Returns
        -------
        list[JobPosting]
            Matched job postings, or offline fixtures on failure.
        """
        if os.getenv("NERAJOB_USAJOBS_OFFLINE", "").strip().lower() in {"1", "true", "yes"}:
            return self._offline(query, location, limit)

        api_key = os.getenv("NERAJOB_USAJOBS_API_KEY", "").strip()
        if not api_key:
            return self._offline(query, location, limit)

        headers = {
            "Host": "data.usajobs.gov",
            "Authorization-Key": api_key,
            "User-Agent": user_agent(),
            "Accept": "application/json",
        }

        params: dict[str, str | int] = {
            "ResultsPerPage": max(1, min(limit, 500)),
            "Page": 1,
        }
        if query.strip():
            params["Keyword"] = query.strip()
        if location.strip():
            params["LocationName"] = location.strip()

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

        result_container = payload.get("SearchResult") if isinstance(payload, dict) else {}
        items = result_container.get("SearchResultItems") if isinstance(result_container, dict) else []
        if not isinstance(items, list):
            return self._offline(query, location, limit)

        q = query.strip().lower()
        loc = location.strip().lower()
        jobs: list[JobPosting] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            posting = self._posting_from_api(item)
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

    # 鈹€鈹€ helpers 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

    def _posting_from_api(self, item: dict) -> JobPosting | None:
        """Convert a USAJOBS API SearchResultItem to a JobPosting."""
        descriptor = item.get("MatchedObjectDescriptor")
        if not isinstance(descriptor, dict):
            return None

        title = str(descriptor.get("PositionTitle") or "").strip()
        if not title:
            return None

        org = str(descriptor.get("OrganizationName") or "Unknown Agency").strip()
        dept = str(descriptor.get("DepartmentName") or "").strip()
        company = f"{dept}" if dept else org

        # Location
        loc_list = descriptor.get("PositionLocation") or []
        if isinstance(loc_list, list) and len(loc_list) > 0:
            first_loc = loc_list[0] if isinstance(loc_list[0], dict) else {}
            place = str(first_loc.get("LocationName") or first_loc.get("CityName") or "United States").strip()
        else:
            place = "United States"

        url = str(descriptor.get("PositionURI") or "").strip()

        # Salary
        remuneration = descriptor.get("PositionRemuneration") or []
        salary_str = ""
        if isinstance(remuneration, list) and len(remuneration) > 0:
            pay = remuneration[0] if isinstance(remuneration[0], dict) else {}
            min_sal = pay.get("MinimumRange")
            max_sal = pay.get("MaximumRange")
            interval = str(pay.get("RateIntervalCode") or "")
            interval_label = "/year" if interval in ("PA", "Per Year") else ""
            if min_sal or max_sal:
                lo = f"${float(min_sal):,.0f}" if min_sal else ""
                hi = f"${float(max_sal):,.0f}" if max_sal else ""
                salary_str = f"{lo} - {hi}{interval_label}" if lo and hi else (lo or hi)

        # Description (from FormattedDescription or UserArea.JobSummary)
        desc = ""
        formatted_desc = descriptor.get("PositionFormattedDescription") or []
        if isinstance(formatted_desc, list):
            for entry in formatted_desc:
                if isinstance(entry, dict) and entry.get("Label") == "Dynamic Teaser":
                    desc = str(entry.get("Content") or "")
                    break
        if not desc:
            user_area = descriptor.get("UserArea") or {}
            details = user_area.get("Details") if isinstance(user_area, dict) else {}
            if isinstance(details, dict):
                desc = str(details.get("JobSummary") or "")

        desc = desc.strip()[:4000]

        # Tags / categories
        tags: list[str] = []
        categories = descriptor.get("JobCategory") or []
        if isinstance(categories, list):
            for cat in categories:
                if isinstance(cat, dict):
                    name = str(cat.get("Name") or "").strip().lower()
                    if name:
                        tags.append(name.replace(" ", "-"))

        schedule = descriptor.get("PositionSchedule") or []
        if isinstance(schedule, list) and len(schedule) > 0:
            if isinstance(schedule[0], dict):
                sname = str(schedule[0].get("Name") or "").strip().lower()
                if sname:
                    tags.append(sname.replace(" ", "-"))

        tags = tags[:20]

        # Remote indicator
        remote = False
        remote_indicator = descriptor.get("RemoteIndicator")
        if isinstance(remote_indicator, str) and remote_indicator.lower() == "true":
            remote = True
        if not remote and "remote" in place.lower():
            remote = True

        raw_id = str(descriptor.get("PositionID") or descriptor.get("MatchedObjectId") or title)
        digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]

        return JobPosting(
            id=f"{self.name}-{digest}",
            source=self.name,
            title=title,
            company=company,
            location=place,
            url=url,
            description=desc,
            tags=tags,
            salary=salary_str,
            remote=remote,
            raw=descriptor,
        )

    def _offline(self, query: str, location: str, limit: int) -> list[JobPosting]:
        """Return deterministic offline fixtures filtered by query + location."""
        q = query.strip().lower()
        loc = location.strip().lower()
        jobs: list[JobPosting] = []
        for title, company, place, tags, url, salary, desc in _OFFLINE:
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
                    salary=salary,
                    remote="remote" in place.lower(),
                )
            )
            if len(jobs) >= limit:
                break
        if not jobs and not q:
            for title, company, place, tags, url, salary, desc in _OFFLINE[:limit]:
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
                        salary=salary,
                        remote="remote" in place.lower(),
                    )
                )
        return jobs
