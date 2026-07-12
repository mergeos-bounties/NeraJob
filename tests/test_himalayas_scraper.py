"""Tests for the Himalayas scraper."""
import pytest
from unittest.mock import patch, MagicMock
import httpx

from nerajob.scrapers.himalayas import HimalayasScraper

SAMPLE_API_RESPONSE = {
    "updatedAt": "2026-07-13T00:00:00Z",
    "offset": 0,
    "limit": 100,
    "totalCount": 2,
    "jobs": [
        {
            "id": "h-123",
            "title": "Senior Python Engineer",
            "companyName": "PyBerlins",
            "companySlug": "pyberlins",
            "employmentType": "Full Time",
            "minSalary": 100000,
            "maxSalary": 140000,
            "salaryPeriod": "annual",
            "locationRestrictions": [],
            "categories": ["Software Engineering", "Python"],
            "parentCategories": ["Engineering"],
            "seniority": ["Senior"],
            "excerpt": "Build Python services at scale.",
            "link": "https://himalayas.app/jobs/senior-python-engineer-pyberlins",
        },
        {
            "id": "h-456",
            "title": "Go Developer",
            "companyName": "GoRemote",
            "companySlug": "goremote",
            "employmentType": "Full Time",
            "minSalary": None,
            "maxSalary": 130000,
            "salaryPeriod": "annual",
            "locationRestrictions": ["United States"],
            "categories": ["Backend"],
            "parentCategories": ["Engineering"],
            "seniority": ["Mid-Level"],
            "excerpt": "Build Go services.",
            "link": "https://himalayas.app/jobs/go-developer-goremote",
        },
        {
            "id": "h-789",
            "title": "Java Lead",
            "companyName": "JavaLabs",
            "companySlug": "javalabs",
            "employmentType": "Full Time",
            "minSalary": None,
            "maxSalary": None,
            "salaryPeriod": "annual",
            "locationRestrictions": ["US", "Canada"],
            "categories": ["Java"],
            "parentCategories": ["Engineering"],
            "seniority": ["Lead"],
            "excerpt": "Lead Java team.",
            "link": "https://himalayas.app/jobs/java-lead-javalabs",
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


def test_himalayas_scraper_filters_python_roles():
    scraper = HimalayasScraper()

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


def test_himalayas_scraper_respects_limit():
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        scraper = HimalayasScraper()
        jobs = scraper.search(query="", limit=1)
        assert len(jobs) <= 1


def test_himalayas_scraper_ids_stable():
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        a = HimalayasScraper().search(query="", limit=5)
        b = HimalayasScraper().search(query="", limit=5)
        assert [j.id for j in a] == [j.id for j in b]


def test_himalayas_scraper_graceful_degradation():
    """Network errors should return empty list, not raise."""
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = Exception("Network error")
        MockClient.return_value = mock_client

        scraper = HimalayasScraper()
        jobs = scraper.search(query="python")
        assert jobs == []


def test_himalayas_scraper_remote_flag():
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        jobs = HimalayasScraper().search(query="python")
        # No location restrictions = remote
        for j in jobs:
            if j.id == "himalayas-" + "h-123"[:12]:  # Only the python job has no restrictions
                assert j.remote is True


def test_himalayas_scraper_salary_format():
    with patch("httpx.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MockResponse(SAMPLE_API_RESPONSE)
        MockClient.return_value = mock_client

        jobs = HimalayasScraper().search(query="", limit=5)
        # First job has both min and max
        py_job = next((j for j in jobs if "python" in j.title.lower()), None)
        assert py_job is not None
        assert "100,000" in py_job.salary or "140,000" in py_job.salary
        # Third job has no salary
        java_job = next((j for j in jobs if "java" in j.title.lower()), None)
        assert java_job is not None
        assert java_job.salary == ""