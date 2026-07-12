"""Tests for the Remotive scraper."""
import pytest
from unittest.mock import patch, MagicMock
import httpx

from nerajob.scrapers.remotive import RemotiveScraper

SAMPLE_API_RESPONSE = {
    "job-count": 3,
    "total-job-count": 3,
    "jobs": [
        {
            "id": 2091056,
            "url": "https://remotive.com/remote-jobs/software-dev/some-role-2091056",
            "title": "Senior Python Engineer",
            "company_name": "PyTech GmbH",
            "tags": ["python", "fastapi", "aws"],
            "job_type": "full_time",
            "publication_date": "2026-07-09T14:45:43",
            "candidate_required_location": "Europe",
            "salary": "$100k - $140k",
            "description": "<p>Build Python APIs with FastAPI.</p>",
        },
        {
            "id": 2091057,
            "url": "https://remotive.com/remote-jobs/software-dev/other-role-2091057",
            "title": "Backend Developer (Go)",
            "company_name": "GoCorp",
            "tags": ["go", "kubernetes"],
            "job_type": "full_time",
            "publication_date": "2026-07-09T14:45:43",
            "candidate_required_location": "Worldwide",
            "salary": "$90k - $130k",
            "description": "<p>Build Go microservices.</p>",
        },
        {
            "id": 2091058,
            "url": "https://remotive.com/remote-jobs/software-dev/java-role-2091058",
            "title": "Java Developer",
            "company_name": "JavaCo",
            "tags": ["java", "spring"],
            "job_type": "full_time",
            "publication_date": "2026-07-09T14:45:43",
            "candidate_required_location": "US only",
            "salary": "",
            "description": "<p>Java microservices.</p>",
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


def test_remotive_scraper_filters_python_roles():
    scraper = RemotiveScraper()

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
    # Java entry should be filtered
    assert all("java" not in j.title.lower() for j in jobs)


def test_remotive_scraper_respects_limit():
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        scraper = RemotiveScraper()
        jobs = scraper.search(query="", limit=1)
        assert len(jobs) <= 1


def test_remotive_scraper_ids_stable():
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        a = RemotiveScraper().search(query="", limit=5)
        b = RemotiveScraper().search(query="", limit=5)
        assert [j.id for j in a] == [j.id for j in b]


def test_remotive_scraper_graceful_degradation():
    """Network errors should return empty list, not raise."""
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = Exception("Network error")
        MockClient.return_value = mock_client

        scraper = RemotiveScraper()
        jobs = scraper.search(query="python")
        assert jobs == []


def test_remotive_scraper_remote_flag():
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        jobs = RemotiveScraper().search(query="python")
        # Worldwide/Europe → remote
        for j in jobs:
            assert j.remote is True


def test_remotive_scraper_job_type_normalised():
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        jobs = RemotiveScraper().search(query="", limit=5)
        assert all("Full-time" in j.tags for j in jobs)