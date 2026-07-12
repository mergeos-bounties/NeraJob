"""Tests for the Arbeitnow scraper."""
import pytest
from unittest.mock import patch, MagicMock
import httpx

from nerajob.scrapers.arbeitnow import ArbeitnowScraper

# Sample API response fixture
SAMPLE_API_RESPONSE = {
    "data": [
        {
            "slug": "senior-python-engineer-berlin-123",
            "company_name": "TechBerlin GmbH",
            "title": "Senior Python Engineer",
            "description": "<p>Join our team building APIs.</p>",
            "remote": True,
            "url": "https://www.arbeitnow.com/jobs/senior-python-engineer-berlin-123",
            "tags": ["python", "fastapi", "apis"],
            "job_types": ["Full-time"],
            "location": "Berlin, Germany",
            "created_at": 1783866629,
        },
        {
            "slug": "backend-dev-remote-456",
            "company_name": "RemoteEU AG",
            "title": "Backend Developer (Python)",
            "description": "<p>Build scalable services.</p>",
            "remote": True,
            "url": "https://www.arbeitnow.com/jobs/backend-dev-remote-456",
            "tags": ["python", "django"],
            "job_types": ["Contract"],
            "location": "Germany",
            "created_at": 1783865630,
        },
        {
            "slug": "java-dev-789",
            "company_name": "JavaCorp",
            "title": "Java Developer",
            "description": "<p>Java role.</p>",
            "remote": False,
            "url": "https://www.arbeitnow.com/jobs/java-dev-789",
            "tags": ["java"],
            "job_types": ["Full-time"],
            "location": "Munich",
            "created_at": 1783864630,
        },
    ],
    "links": {},
    "meta": {},
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


def test_arbeitnow_scraper_filters_python_roles():
    scraper = ArbeitnowScraper()

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


def test_arbeitnow_scraper_respects_limit():
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        scraper = ArbeitnowScraper()
        jobs = scraper.search(query="", limit=1)
        assert len(jobs) <= 1


def test_arbeitnow_scraper_ids_stable():
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        a = ArbeitnowScraper().search(query="", limit=5)
        b = ArbeitnowScraper().search(query="", limit=5)
        assert [j.id for j in a] == [j.id for j in b]


def test_arbeitnow_scraper_graceful_degradation():
    """Network errors should return empty list, not raise."""
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = Exception("Network error")
        MockClient.return_value = mock_client

        scraper = ArbeitnowScraper()
        jobs = scraper.search(query="python")
        assert jobs == []


def test_arbeitnow_scraper_remote_flag():
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        jobs = ArbeitnowScraper().search(query="python")
        for j in jobs:
            assert j.remote is True