"""
Opire scraper — open-source bounty platform.

Source: https://api.opire.dev/rewards
Public API — no auth required.
"""
from __future__ import annotations

import hashlib
import re

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper


class OpireScraper(BaseScraper):
    """
    Opire public bounty API adapter.

    API: GET https://api.opire.dev/rewards?status=open&limit=100
    Returns bounty listings from Opire's GitHub-integrated bounty platform.
    No auth required — public endpoint.
    """
    name = "opire"
    API_URL = "https://api.opire.dev/rewards"

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

        try:
            with httpx.Client(timeout=http_timeout(), headers=headers, follow_redirects=True) as client:
                resp = client.get(self.API_URL, params={"status": "open", "limit": 100})
                resp.raise_for_status()
                data = resp.json()

            items = data if isinstance(data, list) else []
            for item in items:
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

        except Exception:
            return []

        return jobs[:limit]

    def _parse(self, item: dict) -> JobPosting | None:
        url = str(item.get("url") or "")
        if not url:
            return None

        # Extract repo and issue number from GitHub URL
        # e.g. https://github.com/owner/repo/issues/123
        m = re.search(r"github\.com/([^/]+)/([^/]+)/issues/(\d+)", url)
        if not m:
            return None

        owner, repo_name, issue_num = m.group(1), m.group(2), m.group(3)

        # Build stable id
        raw_id = f"{owner}-{repo_name}-{issue_num}"
        digest = hashlib.sha1(raw_id.encode()).hexdigest()[:12]

        title = str(item.get("title") or f"Issue #{issue_num}").strip()
        if not title:
            return None

        # Bounty amount
        pending = item.get("pendingPrice") or {}
        cents = int(pending.get("value", 0))
        dollars = cents / 100.0
        bounty_str = f"${dollars:.0f}" if dollars > 0 else ""

        org_info = item.get("organization") or {}
        company = str(org_info.get("name") or owner)

        languages = item.get("programmingLanguages") or []
        tags: list[str] = [str(lang) for lang in languages if lang]

        if bounty_str:
            tags.append(bounty_str)

        # Description
        description = (
            f"Opire bounty platform: {url}\n"
            f"Bounty: {bounty_str}\n"
            f"Organization: {company}\n"
            f"Languages: {', '.join(languages)}"
        )

        return JobPosting(
            id=f"opire-{digest}",
            source=self.name,
            title=title,
            company=company,
            location="Remote",
            url=url,
            description=description,
            tags=tags[:20],
            salary=bounty_str,
            remote=True,
            raw=item,
        )