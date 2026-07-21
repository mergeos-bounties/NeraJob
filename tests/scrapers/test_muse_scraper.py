import unittest
from unittest.mock import patch, MagicMock
from src.nerajob.scrapers.muse_scraper import MuseScraper

class TestMuseScraper(unittest.TestCase):
    """Tests for MuseScraper."""

    @patch('requests.get')
    def test_search_success(self, mock_get):
        """Test successful job search."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "name": "Software Engineer",
                    "company": {"name": "Tech Corp"},
                    "locations": [{"name": "New York"}],
                    "refs": {"landing_page": "https://example.com/job1"},
                    "contents": "Job description",
                    "tags": [{"name": "Python"}, {"name": "Django"}]
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        scraper = MuseScraper()
        jobs = scraper.search("Software Engineering", "New York", 1)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["title"], "Software Engineer")
        self.assertEqual(jobs[0]["company"], "Tech Corp")

    @patch('requests.get')
    def test_search_error(self, mock_get):
        """Test error handling."""
        mock_get.side_effect = Exception("API error")

        scraper = MuseScraper()
        jobs = scraper.search("Software Engineering", "New York", 1)

        self.assertEqual(len(jobs), 0)