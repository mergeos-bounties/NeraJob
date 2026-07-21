import pytest
from unittest.mock import patch, MagicMock
from nerajob.scrapers.greenhouse import GreenhouseScraper

@pytest.fixture
def mock_response():
    return {
        'jobs': [
            {
                'id': 1,
                'title': 'Python Developer',
                'location': {'name': 'Remote'},
                'absolute_url': 'https://example.com/job1'
            },
            {
                'id': 2,
                'title': 'Java Developer',
                'location': {'name': 'New York'},
                'absolute_url': 'https://example.com/job2'
            }
        ]
    }

def test_greenhouse_search(mock_response):
    with patch('requests.get') as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        scraper = GreenhouseScraper(['test_board'])
        results = scraper.search('Python', 'Remote', 1)

        assert len(results) == 1
        assert results[0]['title'] == 'Python Developer'
        assert mock_get.call_count == 1

def test_greenhouse_search_error():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception('API Error')

        scraper = GreenhouseScraper(['test_board'])
        results = scraper.search('Python')

        assert len(results) == 0