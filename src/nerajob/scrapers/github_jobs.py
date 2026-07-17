"""GitHub Jobs public API adapter (with offline sample fallback)."""

from __future__ import annotations

import hashlib
import os

import httpx

from nerajob.config import http_timeout, user_agent
from nerajob.models import JobPosting
from nerajob.scrapers.base import BaseScraper

# Offline fixtures when network fails or NERAJOB_GITHUB_OFFLINE=1
_OFFLINE = [
    (
        "Senior Python Developer",
        "GitHub Demo Co",
        "San Francisco, CA",
        ["python", "django", "fastapi", "postgresql"],
        "https://jobs.github.com/positions/demo-python",
    ),
    (
        "Full Stack Engineer",
        "OpenSource Inc",
        "Remote",
        ["javascript", "react", "node", "typescript"],
        "https://jobs.github.com/positions/demo-fullstack",
    ),
    (
        "DevOps Engineer",
        "CloudNative Corp",
        "New York, NY",
        ["docker", "kubernetes", "aws", "terraform"],
        "https://jobs.github.com/positions/demo-devops",
    ),
    (
        "Data Scientist",
        "AI Research Lab",
        "Boston, MA",
        ["python", "machine learning", "tensorflow", "pandas"],
        "https://jobs.github.com/positions/demo-datascience",
    ),
    (
        "Mobile Developer",
        "AppWorks",
        "Austin, TX",
        ["flutter", "dart", "ios", "android"],
        "https://jobs.github.com/positions/demo-mobile",
    ),
]


class GitHubJobsScraper(BaseScraper):
    """
    GitHub Jobs public API.
    
    Note: GitHub Jobs API was deprecated in 2022, but this scraper
    demonstrates the pattern for public API integration with proper
    mocking support for tests.
    
    For production use, consider using GitHub's GraphQL API or
    other job board APIs.
    """

    name = "github_jobs"
    API_URL = "https://jobs.github.com/positions.json"

    def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        if os.getenv("NERAJOB_GITHUB_OFFLINE", "").strip() in {"1", "true", "yes"}:
            return self._offline(query, limit)

        headers = {
            "User-Agent": user_agent(),
            "Accept": "application/json",
        }
        
        params = {
            "description": query,
            "full_time": "true",
        }
        
        if location:
            params["location"] = location

        try:
            resp = httpx.get(
                self.API_URL,
                params=params,
                headers=headers,
                timeout=http_timeout(),
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return self._offline(query, limit)

        results: list[JobPosting] = []
        for item in data[:limit]:
            job_id = item.get("id") or hashlib.md5(
                (item.get("title", "") + item.get("company", "")).encode()
            ).hexdigest()[:12]
            
            results.append(
                JobPosting(
                    id=f"github_{job_id}",
                    source=self.name,
                    title=item.get("title", "Untitled"),
                    company=item.get("company", "Unknown"),
                    location=item.get("location", ""),
                    description=item.get("description", ""),
                    tags=[
                        t.strip().lower()
                        for t in (item.get("type") or "").split(",")
                        if t.strip()
                    ] or ["full-time"],
                    url=item.get("url") or item.get("html_url") or "",
                    salary=item.get("salary") or "",
                )
            )

        return results

    def _offline(self, query: str, limit: int) -> list[JobPosting]:
        """Return offline sample data filtered by query."""
        query_lower = query.lower()
        results: list[JobPosting] = []
        
        for title, company, location, tags, url in _OFFLINE:
            if query_lower in title.lower() or query_lower in " ".join(tags).lower():
                results.append(
                    JobPosting(
                        id=f"github_offline_{hashlib.md5(title.encode()).hexdigest()[:8]}",
                        source=self.name,
                        title=title,
                        company=company,
                        location=location,
                        description=f"Offline sample: {title} at {company}",
                        tags=tags,
                        url=url,
                    )
                )
        
        return results[:limit]
