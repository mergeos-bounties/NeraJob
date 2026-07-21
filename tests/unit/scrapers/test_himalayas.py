import unittest
from unittest.mock import patch, MagicMock
from src.nerajob.scrapers.himalayas import HimalayasScraper

class TestHimalayasScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = HimalayasScraper()

    @patch('requests.get')
    def test_search_success(self, mock_get):
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jobs": [
                {
                    "title": "Python Developer",
                    "company": "Tech Corp",
                    "location": "Remote",
                    "url": "https://example.com/job1",
                    "description": "Python job description"
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        jobs = self.scraper.search("python", limit=1)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["title"], "Python Developer")

    @patch('requests.get')
    def test_search_failure(self, mock_get):
        # Mock failed API response
        mock_get.side_effect = Exception("API error")

        jobs = self.scraper.search("python")
        self.assertEqual(len(jobs), 0)

if __name__ == '__main__':
    unittest.main()