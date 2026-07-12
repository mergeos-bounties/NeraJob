from __future__ import annotations

import hashlib

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper


class RemoteOKScraper(BaseScraper):
    """
    Public RemoteOK JSON feed adapter.

    Source: https://remoteok.com/api
    Respect their ToS; this is a thin example live adapter.
    """

    name = "remoteok"
    API_URL = "https://remoteok.com/api"

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        headers = {
            "User-Agent": user_agent(),
            "Accept": "application/json",
        }
        try:
            with httpx.Client(timeout=http_timeout(), headers=headers, follow_redirects=True) as client:
                response = client.get(self.API_URL)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            # Network or API failure should not crash the CLI; caller can fall back.
            return []

        if not isinstance(payload, list):
            return []

        q = query.strip().lower()
        jobs: list[JobPosting] = []
        for item in payload:
            if not isinstance(item, dict) or "id" not in item:
                continue
            title = str(item.get("position") or item.get("title") or "").strip()
            company = str(item.get("company") or "").strip()
            if not title:
                continue
            tags = [str(t).lower() for t in (item.get("tags") or []) if t]
            hay = f"{title} {company} {' '.join(tags)} {item.get('description', '')}".lower()
            if q and q not in hay:
                continue
            loc = str(item.get("location") or "Remote")
            url = str(item.get("url") or item.get("apply_url") or "")
            raw_id = str(item.get("id"))
            digest = hashlib.sha1(f"{self.name}:{raw_id}".encode()).hexdigest()[:12]
            jobs.append(
                JobPosting(
                    id=f"remoteok-{digest}",
                    source=self.name,
                    title=title,
                    company=company or "Unknown",
                    location=loc or "Remote",
                    url=url,
                    description=_strip_html(str(item.get("description") or ""))[:4000],
                    tags=tags[:20],
                    salary=str(item.get("salary") or ""),
                    remote=True,
                    raw={"remoteok_id": raw_id},
                )
            )
            if len(jobs) >= limit:
                break
        return jobs


def _strip_html(value: str) -> str:
    # Lightweight strip without requiring BS4 for API JSON text.
    import re

    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", text).strip()
