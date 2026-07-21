import unittest
from unittest.mock import patch, MagicMock
from src.nerajob.scrapers.lever import LeverScraper
from src.nerajob.models import JobPosting

class TestLeverScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = LeverScraper()

    @patch('requests.get')
    def test_search_success(self, mock_get):
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [
                {
                    'text': 'Python Developer',
                    'categories': {'location': 'Remote'},
                    'hostedUrl': 'https://example.com/job1'
                },
                {
                    'text': 'Java Developer',
                    'categories': {'location': 'New York'},
                    'hostedUrl': 'https://example.com/job2'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test search
        results = self.scraper.search('Python', limit=1)

        # Assertions
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], JobPosting)
        self.assertEqual(results[0].title, 'Python Developer')

    @patch('requests.get')
    def test_search_error(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        results = self.scraper.search('Python')

        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main()