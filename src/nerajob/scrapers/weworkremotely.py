"""We Work Remotely public feed adapter with offline fallback."""

from __future__ import annotations

import hashlib
import os
import re
import xml.etree.ElementTree as ET

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper

_OFFLINE = [
    (
        "Senior Full-Stack Engineer",
        "WWR Demo Labs",
        "Remote",
        ["python", "react", "remote"],
        "https://weworkremotely.com/remote-jobs/demo-fullstack",
    ),
    (
        "Remote Site Reliability Engineer",
        "Orbit Cloud",
        "Worldwide",
        ["sre", "kubernetes", "python"],
        "https://weworkremotely.com/remote-jobs/demo-sre",
    ),
    (
        "QA Automation Engineer",
        "ShipSure",
        "Remote",
        ["qa", "pytest", "selenium"],
        "https://weworkremotely.com/remote-jobs/demo-qa-automation",
    ),
]


class WeWorkRemotelyScraper(BaseScraper):
    """https://weworkremotely.com/categories/remote-programming-jobs.rss"""

    name = "weworkremotely"
    RSS_URL = "https://weworkremotely.com/categories/remote-programming-jobs.rss"

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        if os.getenv("NERAJOB_WWR_OFFLINE", "").strip().lower() in {"1", "true", "yes"}:
            return self._offline(query, limit)
        headers = {"User-Agent": user_agent(), "Accept": "application/rss+xml, application/xml, text/xml"}
        try:
            with httpx.Client(timeout=http_timeout(), headers=headers, follow_redirects=True) as client:
                response = client.get(self.RSS_URL)
                response.raise_for_status()
                text = response.text
        except Exception:
            return self._offline(query, limit)

        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            return self._offline(query, limit)

        items = root.findall(".//item")
        q = query.strip().lower()
        jobs: list[JobPosting] = []
        for item in items:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            desc = (item.findtext("description") or "").strip()
            if not title:
                continue
            # WWR titles often "Company: Role"
            company = "Unknown"
            role = title
            if ":" in title:
                company, role = [p.strip() for p in title.split(":", 1)]
            hay = f"{title} {desc}".lower()
            if q and q not in hay:
                continue
            tags = re.findall(r"[a-zA-Z+#.]{2,}", desc.lower())[:12]
            digest = hashlib.sha1(f"{self.name}:{link or title}".encode()).hexdigest()[:12]
            jobs.append(
                JobPosting(
                    id=f"wwr-{digest}",
                    source=self.name,
                    title=role or title,
                    company=company,
                    location="Remote",
                    url=link or f"https://weworkremotely.com/remote-jobs/{digest}",
                    description=re.sub(r"<[^>]+>", " ", desc)[:4000],
                    tags=tags,
                    remote=True,
                    raw={"rss_title": title},
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
            digest = hashlib.sha1(f"{self.name}:{title}".encode()).hexdigest()[:12]
            out.append(
                JobPosting(
                    id=f"wwr-{digest}",
                    source=self.name,
                    title=title,
                    company=company,
                    location=place,
                    url=url,
                    description=f"{title} at {company} (offline sample).",
                    tags=tags,
                    remote=True,
                )
            )
            if len(out) >= limit:
                break
        if not out and not q:
            for title, company, place, tags, url in _OFFLINE[:limit]:
                digest = hashlib.sha1(f"{self.name}:{title}".encode()).hexdigest()[:12]
                out.append(
                    JobPosting(
                        id=f"wwr-{digest}",
                        source=self.name,
                        title=title,
                        company=company,
                        location=place,
                        url=url,
                        description=f"{title} at {company} (offline sample).",
                        tags=tags,
                        remote=True,
                    )
                )
        return out
