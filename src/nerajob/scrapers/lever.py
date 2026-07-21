import requests
from typing import List, Dict, Optional
from .base import BaseScraper
from ..models import JobPosting

class LeverScraper(BaseScraper):
    """Scraper for Lever public postings API."""

    def __init__(self):
        super().__init__()
        self.base_url = "https://api.lever.co/v0/postings"

    def search(self, query: str, location: Optional[str] = None, limit: int = 10) -> List[JobPosting]:
        """Search for job postings on Lever."""
        company = self._get_company_from_config()
        url = f"{self.base_url}/{company}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            jobs = []
            for posting in data.get('data', [])[:limit]:
                if query.lower() in posting.get('text', '').lower():
                    job = JobPosting(
                        title=posting.get('text', ''),
                        company=company,
                        location=posting.get('categories', {}).get('location', ''),
                        description=posting.get('text', ''),
                        url=posting.get('hostedUrl', ''),
                        source='lever'
                    )
                    jobs.append(job)

            return jobs
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Lever postings: {e}")
            return []

    def _get_company_from_config(self) -> str:
        """Get company name from configuration."""
        # This would be implemented based on the repository's config system
        # For now, we'll return a placeholder
        return "example-company"