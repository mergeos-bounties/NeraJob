import requests
from typing import List, Dict, Optional
from .base import BaseScraper

class HimalayasScraper(BaseScraper):
    """Scraper for Himalayas.app public remote jobs API."""

    def __init__(self):
        super().__init__("himalayas")
        self.base_url = "https://api.himalayas.app/v1/jobs"

    def search(self, query: str, location: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Search for remote jobs matching the query."""
        params = {
            "query": query,
            "limit": limit,
            "remote": True
        }

        if location:
            params["location"] = location

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            jobs = response.json().get("jobs", [])

            # Format jobs to match our standard structure
            formatted_jobs = []
            for job in jobs:
                formatted_jobs.append({
                    "title": job.get("title"),
                    "company": job.get("company"),
                    "location": job.get("location"),
                    "url": job.get("url"),
                    "description": job.get("description"),
                    "source": self.name
                })

            return formatted_jobs[:limit]

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching jobs from Himalayas: {e}")
            return []