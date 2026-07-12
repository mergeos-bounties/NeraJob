import requests
from typing import List, Dict, Any
from .base import BaseScraper

class HimalayasScraper(BaseScraper):
    name = "himalayas"

    def search(self, query: str, location: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        url = "https://himalayas.app/jobs/api"
        params = {"keyword": query, "limit": limit}
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = []
            for job in data.get("data", [])[:limit]:
                results.append({
                    "title": job.get("title", ""),
                    "company": job.get("company", {}).get("name", ""),
                    "location": job.get("city", "") or job.get("country", ""),
                    "remote": job.get("locationRestrictions") == "Worldwide",
                    "url": job.get("url", ""),
                    "source": "himalayas"
                })
            return results
        except Exception:
            return []