import requests
from typing import List, Dict, Optional
from .base_scraper import BaseScraper

class MuseScraper(BaseScraper):
    """Scraper for The Muse jobs API."""

    def __init__(self):
        super().__init__()
        self.base_url = "https://www.themuse.com/api/public/jobs"
        self.name = "muse"

    def search(self, query: str, location: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Search for jobs using The Muse API."""
        params = {
            "page": 1,
            "descending": "true",
            "category": query,
            "location": location,
            "limit": limit
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            jobs = []
            for job in data.get("results", []):
                jobs.append({
                    "title": job.get("name"),
                    "company": job.get("company", {}).get("name"),
                    "location": job.get("locations", [{}])[0].get("name"),
                    "url": job.get("refs", {}).get("landing_page"),
                    "description": job.get("contents"),
                    "tags": [tag.get("name") for tag in job.get("tags", [])]
                })

            return jobs[:limit]

        except requests.exceptions.RequestException as e:
            print(f"Error fetching jobs from Muse: {e}")
            return []