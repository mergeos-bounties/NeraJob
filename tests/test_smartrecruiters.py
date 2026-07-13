"""Tests for the SmartRecruiters scraper."""

import httpx

from nerajob.scrapers.registry import available_scrapers
from nerajob.scrapers.smartrecruiters import SmartRecruitersScraper


def test_smartrecruiters_offline_filters_python_roles(monkeypatch):
    monkeypatch.setenv("NERAJOB_SMARTRECRUITERS_OFFLINE", "1")

    jobs = SmartRecruitersScraper().search(query="python", limit=10)

    assert jobs
    assert all(j.source == "smartrecruiters" for j in jobs)
    for job in jobs:
        assert (
            "python" in f"{job.title} {job.company} {job.description} {' '.join(job.tags)}".lower()
        )


def test_smartrecruiters_mocked_public_postings(monkeypatch):
    monkeypatch.setenv("NERAJOB_SMARTRECRUITERS_COMPANIES", "Acme")
    payload = {
        "content": [
            {
                "id": "backend-python",
                "name": "Senior Python Engineer",
                "company": {"name": "Acme"},
                "location": {"city": "Berlin", "country": "Germany"},
                "department": {"label": "Engineering"},
                "ref": "REF-1",
                "postingUrl": "https://jobs.smartrecruiters.com/Acme/backend-python",
                "jobAd": {"sections": {"jobDescription": {"text": "Build Python APIs."}}},
            },
            {
                "id": "frontend",
                "name": "Frontend Engineer",
                "company": {"name": "Acme"},
                "location": {"city": "Paris", "country": "France"},
                "department": {"label": "Engineering"},
                "postingUrl": "https://jobs.smartrecruiters.com/Acme/frontend",
            },
        ]
    }

    def handler(request):
        assert request.url.path == "/v1/companies/Acme/postings"
        assert request.url.params["q"] == "python"
        assert request.url.params["limit"] == "5"
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client

    def client_factory(**kwargs):
        kwargs["transport"] = transport
        return original_client(**kwargs)

    monkeypatch.setattr(httpx, "Client", client_factory)

    jobs = SmartRecruitersScraper().search(query="python", location="berlin", limit=5)

    assert len(jobs) == 1
    assert jobs[0].id.startswith("smartrecruiters-")
    assert jobs[0].title == "Senior Python Engineer"
    assert jobs[0].company == "Acme"
    assert jobs[0].location == "Berlin, Germany"
    assert jobs[0].url == "https://jobs.smartrecruiters.com/Acme/backend-python"
    assert "engineering" in jobs[0].tags
    assert "Python APIs" in jobs[0].description


def test_smartrecruiters_registered():
    assert "smartrecruiters" in available_scrapers()
