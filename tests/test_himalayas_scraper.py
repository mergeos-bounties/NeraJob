import pytest
from unittest.mock import patch
from src.nerajob.scrapers.himalayas import HimalayasScraper

def test_search():
    mock_response = {
        "data": [
            {"title": "Python Dev", "company": {"name": "Tech Co"}, "url": "https://example.com"}
        ]
    }
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.raise_for_status.return_value = None
        scraper = HimalayasScraper()
        results = scraper.search("python", limit=5)
        assert len(results) == 1
        assert results[0]["title"] == "Python Dev"