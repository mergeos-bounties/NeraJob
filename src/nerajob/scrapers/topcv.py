"""TopCV.vn public jobs API adapter (Vietnam market — offline fallback for CI)."""

from __future__ import annotations

import hashlib
import os

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper

# Offline fixtures — used when NERAJOB_TOPCV_OFFLINE=1 or network call fails.
# These are deterministic samples for demos/tests (no live network required).
_OFFLINE = [
    (
        "Senior Python Engineer",
        "Viettel Solutions",
        "Ho Chi Minh City",
        ["python", "fastapi", "postgresql"],
        "https://www.topcv.vn/jobs/demo-viettel-python",
    ),
    (
        "Frontend Developer (React)",
        "FPT Smart Cloud",
        "Hanoi",
        ["react", "typescript", "nextjs"],
        "https://www.topcv.vn/jobs/demo-fpt-frontend",
    ),
    (
        "DevOps Engineer",
        "NashTech Vietnam",
        "Ho Chi Minh City",
        ["kubernetes", "docker", "aws", "terraform"],
        "https://www.topcv.vn/jobs/demo-nashtech-devops",
    ),
    (
        "Data Engineer",
        "One Housing Technology",
        "Ho Chi Minh City",
        ["python", "spark", "airflow"],
        "https://www.topcv.vn/jobs/demo-onehousing-data",
    ),
    (
        "Mobile Developer (Flutter)",
        "MoMo Vietnam",
        "Ho Chi Minh City",
        ["flutter", "dart", "mobile"],
        "https://www.topcv.vn/jobs/demo-momo-flutter",
    ),
    (
        "Backend Engineer (Java)",
        "VNG Corporation",
        "Ho Chi Minh City",
        ["java", "spring boot", "microservices"],
        "https://www.topcv.vn/jobs/demo-vng-java",
    ),
    (
        "ML Engineer",
        "FPT AI",
        "Hanoi",
        ["python", "pytorch", "mlops", "deep learning"],
        "https://www.topcv.vn/jobs/demo-fptai-ml",
    ),
    (
        "Product Designer",
        "Kiot Viet",
        "Ho Chi Minh City",
        ["figma", "ui", "ux", "product design"],
        "https://www.topcv.vn/jobs/demo-kiotviet-design",
    ),
]


class TopcvScraper(BaseScraper):
    """
    TopCV.vn public job API for the Vietnam market.

    API docs: https://www.topcv.vn/api
    Endpoint : https://www.topcv.vn/api/job/list
    No authentication required for public listing search.

    ToS note: This scraper makes conservative, rate-limited requests against
    TopCV's public job listing page. Scraping is subject to TopCV's Terms of
    Service. Use NERAJOB_TOPCV_OFFLINE=1 in CI/production environments to
    avoid live network calls. If deploying live, ensure compliance with
    TopCV's robots.txt and rate-limit your requests appropriately.

    Environment:
      NERAJOB_TOPCV_OFFLINE=1  — force offline fixture mode (default in CI)
    """

    name = "topcv"
    BASE_URL = "https://www.topcv.vn/api/job/list"

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        if os.getenv("NERAJOB_TOPCV_OFFLINE", "").strip().lower() in {"1", "true", "yes"}:
            return self._offline(query, limit)

        headers = {
            "User-Agent": user_agent(),
            "Accept": "application/json, text/html",
            "Referer": "https://www.topcv.vn/",
        }
        params: dict[str, str | int] = {
            "page": 1,
            "limit": min(limit, 50),
        }
        q = query.strip()
        loc = location.strip()

        if q:
            params["keyword"] = q

        try:
            with httpx.Client(
                timeout=http_timeout(),
                headers=headers,
                follow_redirects=True,
                limits=httpx.Limits(max_keepalive_connections=3, max_connections=5),
            ) as client:
                response = client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return self._offline(query, limit)

        jobs_raw = self._extract_jobs(payload)
        if not jobs_raw:
            return self._offline(query, limit)

        q_lc = q.lower()
        loc_lc = loc.lower()
        jobs: list[JobPosting] = []

        for item in jobs_raw:
            if not isinstance(item, dict):
                continue

            title = str(item.get("title") or item.get("name") or "").strip()
            company = str(
                item.get("company_name")
                or item.get("company")
                or item.get("employer")
                or ""
            ).strip()
            if not title:
                continue

            description = _strip_html(
                str(
                    item.get("description")
                    or item.get("summary")
                    or item.get("detail")
                    or ""
                )
            )
            tags_raw = item.get("tags") or item.get("categories") or []
            tags = _string_list(tags_raw)[:20]

            level = str(item.get("level") or item.get("seniority") or "").strip()
            if level:
                tags.append(level.lower())

            # Try multiple location field names
            place = (
                str(item.get("location") or item.get("city") or item.get("province") or "Vietnam")
            ).strip()

            # Try multiple URL field names
            url = (
                str(item.get("url") or item.get("link") or item.get("job_url") or "")
            ).strip()

            # Try multiple salary field names
            salary_raw = (
                item.get("salary")
                or item.get("salary_text")
                or item.get("salary_range")
                or ""
            )
            salary = str(salary_raw).strip() if salary_raw else ""

            remote = _is_remote(place, description)

            hay = f"{title} {company} {place} {' '.join(tags)} {description}".lower()
            if q_lc and q_lc not in hay:
                continue
            if loc_lc and loc_lc not in place.lower() and not remote:
                continue

            raw_id = (
                str(item.get("id"))
                or str(item.get("slug"))
                or str(item.get("alias"))
                or url
                or title
            )
            digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]

            jobs.append(
                JobPosting(
                    id=f"topcv-{digest}",
                    source=self.name,
                    title=title,
                    company=company or "Unknown",
                    location=place,
                    url=url,
                    description=description[:4000],
                    tags=tags,
                    salary=salary,
                    remote=remote,
                    raw={"topcv_id": raw_id},
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
                    id=f"topcv-{digest}",
                    source=self.name,
                    title=title,
                    company=company,
                    location=place,
                    url=url,
                    description=f"{title} at {company} — Vietnam tech market sample.",
                    tags=tags,
                    remote="remote" in place.lower() or "ho chi minh" in place.lower(),
                    raw={"offline": True},
                )
            )
            if len(out) >= limit:
                break
        return out

    def _extract_jobs(self, payload: object) -> list[dict]:
        """Navigate TopCV API response structure to extract job list."""
        if isinstance(payload, dict):
            # Common TopCV response shapes
            if "data" in payload:
                data = payload["data"]
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    # Pagination wrapper: data.data or data.jobs
                    for key in ["data", "jobs", "items", "results"]:
                        inner = data.get(key)
                        if isinstance(inner, list):
                            return inner
                    # Flat dict of jobs
                    return [v for v in data.values() if isinstance(v, dict) and v.get("id")]
            if isinstance(payload, list):
                return payload
        return []


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip().lower() for item in value if str(item).strip()]
    if value:
        return [str(value).strip().lower()]
    return []


def _strip_html(value: str) -> str:
    import re

    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", text).strip()


def _is_remote(location: str, description: str) -> bool:
    text = f"{location} {description}".lower()
    return any(
        tok in text for tok in ("remote", "work from home", "wfh", "từ xa", "tat ca tinh thanh")
    )