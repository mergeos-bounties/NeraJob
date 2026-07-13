"""Tests for The Muse scraper."""
from unittest.mock import patch, MagicMock
import httpx

from nerajob.scrapers.themuse import TheMuseScraper


SAMPLE_API_RESPONSE = {
    "page": 0,
    "page_count": 1,
    "items_per_page": 20,
    "total": 3,
    "results": [
        {
            "id": 123456,
            "name": "Senior Python Engineer",
            "company": {"name": "PyTech Inc"},
            "locations": [{"name": "Remote"}],
            "categories": ["Software Engineering", "Python"],
            "levels": [{"name": "Senior"}],
            "refs": {"landing_page": "https://www.themuse.com/jobs/123456"},
            "contents": "<p>Build Python services at scale.</p>",
        },
        {
            "id": 123457,
            "name": "Go Developer",
            "company": {"name": "GoCorp"},
            "locations": [{"name": "New York, NY"}],
            "categories": ["Backend"],
            "levels": [{"name": "Mid-Level"}],
            "refs": {"landing_page": "https://www.themuse.com/jobs/123457"},
            "contents": "<p>Build Go microservices.</p>",
        },
        {
            "id": 123458,
            "name": "Java Lead",
            "company": {"name": "JavaCo"},
            "locations": [{"name": "San Francisco, CA"}],
            "categories": ["Software Engineering"],
            "levels": [{"name": "Lead"}],
            "refs": {"landing_page": "https://www.themuse.com/jobs/123458"},
            "contents": "<p>Lead Java team.</p>",
        },
    ],
}


class MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=MagicMock(), response=self)

    def json(self):
        return self._json


def test_muse_scraper_filters_python_roles():
    scraper = TheMuseScraper()

    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        jobs = scraper.search(query="python", limit=10)

    assert jobs
    assert all(
        "python" in (j.title.lower() + " " + j.company.lower() + " " + " ".join(j.tags))
        for j in jobs
    )
    assert all("java" not in j.title.lower() for j in jobs)


def test_muse_scraper_respects_limit():
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        scraper = TheMuseScraper()
        jobs = scraper.search(query="", limit=1)
        assert len(jobs) <= 1


def test_muse_scraper_ids_stable():
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        a = TheMuseScraper().search(query="", limit=5)
        b = TheMuseScraper().search(query="", limit=5)
        assert [j.id for j in a] == [j.id for j in b]


def test_muse_scraper_graceful_degradation():
    """Network errors should return empty list, not raise."""
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = Exception("Network error")
        MockClient.return_value = mock_client

        scraper = TheMuseScraper()
        jobs = scraper.search(query="python")
        assert jobs == []


def test_muse_scraper_remote_flag():
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        jobs = TheMuseScraper().search(query="python")
        # Remote location → remote=True
        for j in jobs:
            if "remote" in j.location.lower():
                assert j.remote is True