import unittest
from unittest.mock import patch
from src.nerajob.cli import main

class TestScanCommand(unittest.TestCase):
    """Integration tests for the scan command."""

    @patch('src.nerajob.scrapers.muse_scraper.MuseScraper.search')
    def test_scan_muse(self, mock_search):
        """Test scanning with Muse scraper."""
        mock_search.return_value = [
            {
                "title": "Software Engineer",
                "company": "Tech Corp",
                "location": "New York",
                "url": "https://example.com/job1",
                "description": "Job description",
                "tags": ["Python", "Django"]
            }
        ]

        # This would be replaced with actual CLI testing
        # For now, we just verify the mock is called
        with patch('sys.argv', ['nerajob', 'scan', '--source', 'muse', '-q', 'Software Engineering', '-n', '1']):
            main()

        mock_search.assert_called_once_with("Software Engineering", None, 1)