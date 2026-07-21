import json
import requests
from typing import List, Dict, Optional
from .base import BaseScraper

class GreenhouseScraper(BaseScraper):
    """Scraper for Greenhouse public board API."""

    def __init__(self, board_tokens: List[str]):
        self.board_tokens = board_tokens
        self.base_url = "https://boards-api.greenhouse.io/v1/boards"

    async def search(self, query: str, location: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Search jobs across all configured boards."""
        results = []
        for token in self.board_tokens:
            try:
                url = f"{self.base_url}/{token}/jobs"
                response = requests.get(url)
                response.raise_for_status()
                jobs = response.json().get('jobs', [])

                # Filter and limit results
                filtered = [
                    job for job in jobs
                    if query.lower() in job.get('title', '').lower() or
                    (location and location.lower() in job.get('location', {}).get('name', '').lower())
                ]
                results.extend(filtered[:limit - len(results)])
                if len(results) >= limit:
                    break
            except requests.RequestException as e:
                print(f"Error fetching from board {token}: {e}")
                continue

        return results[:limit]

    @classmethod
    def from_config(cls, config: Dict) -> 'GreenhouseScraper':
        """Initialize from configuration."""
        return cls(config.get('board_tokens', []))