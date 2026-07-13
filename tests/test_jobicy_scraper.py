"""Tests for the Jobicy scraper."""
from unittest.mock import patch, MagicMock
import httpx

from nerajob.scrapers.jobicy import JobicyScraper


SAMPLE_API_RESPONSE = {
    "success": True,
    "apiVersion": "2.0",
    "jobCount": 3,
    "jobs": [
        {
            "id": 149156,
            "url": "https://jobicy.com/jobs/149156-senior-full-stack-engineer-python-react",
            "jobSlug": "149156-senior-full-stack-engineer-python-react",
            "jobTitle": "Senior Full-stack Engineer (Python/React)",
            "companyName": "Truelogic",
            "companyLogo": "https://jobicy.com/logo.png",
            "jobIndustry": ["Software Engineering"],
            "jobType": ["Full-Time"],
            "jobGeo": "LATAM",
            "jobLevel": "Senior",
            "jobExcerpt": "Build Python microservices at scale.",
        },
        {
            "id": 149157,
            "url": "https://jobicy.com/jobs/149157-go-developer-goremote",
            "jobSlug": "149157-go-developer-goremote",
            "jobTitle": "Go Developer",
            "companyName": "GoRemote",
            "companyLogo": "https://jobicy.com/logo2.png",
            "jobIndustry": ["Backend"],
            "jobType": ["Full-Time"],
            "jobGeo": "Worldwide",
            "jobLevel": "Mid-Level",
            "jobExcerpt": "Build Go services.",
        },
        {
            "id": 149158,
            "url": "https://jobicy.com/jobs/149158-java-lead-javalabs",
            "jobSlug": "149158-java-lead-javalabs",
            "jobTitle": "Java Lead",
            "companyName": "JavaLabs",
            "companyLogo": "https://jobicy.com/logo3.png",
            "jobIndustry": ["Software Engineering"],
            "jobType": ["Full-Time"],
            "jobGeo": "US",
            "jobLevel": "Lead",
            "jobExcerpt": "Lead Java team.",
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


def test_jobicy_scraper_filters_python_roles():
    scraper = JobicyScraper()

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


def test_jobicy_scraper_respects_limit():
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        scraper = JobicyScraper()
        jobs = scraper.search(query="", limit=1)
        assert len(jobs) <= 1


def test_jobicy_scraper_ids_stable():
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        a = JobicyScraper().search(query="", limit=5)
        b = JobicyScraper().search(query="", limit=5)
        assert [j.id for j in a] == [j.id for j in b]


def test_jobicy_scraper_graceful_degradation():
    """Network errors should return empty list, not raise."""
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = Exception("Network error")
        MockClient.return_value = mock_client

        scraper = JobicyScraper()
        jobs = scraper.search(query="python")
        assert jobs == []


def test_jobicy_scraper_remote_flag():
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        jobs = JobicyScraper().search(query="", limit=5)
        # Jobicy is a remote jobs platform
        for j in jobs:
            assert j.remote is True