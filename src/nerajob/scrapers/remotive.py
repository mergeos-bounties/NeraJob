import requests
from typing import List, Dict, Any
from .base import BaseScraper

class RemotiveScraper(BaseScraper):
    name = "remotive"

    def search(self, query: str, location: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        url = "https://remotive.com/api/remote-jobs"
        params = {"search": query, "limit": limit}
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = []
            for job in data.get("jobs", [])[:limit]:
                results.append({
                    "title": job.get("title", ""),
                    "company": job.get("company_name", ""),
                    "location": job.get("candidate_required_location", ""),
                    "remote": True,
                    "url": job.get("url", ""),
                    "source": "remotive"
                })
            return results
        except Exception:
            return []
