"""Tests for the Findwork.dev scraper (issue #6)."""
from __future__ import annotations

import pytest

from nerajob.scrapers.findwork import FindworkScraper
from nerajob.scrapers.registry import available_scrapers, get_scraper


def test_findwork_registered() -> None:
    assert "findwork" in available_scrapers()


def test_findwork_get_scraper_returns_findwork_instance() -> None:
    scraper = get_scraper("findwork")
    assert isinstance(scraper, FindworkScraper)
    assert scraper.name == "findwork"


def test_findwork_offline_returns_jobs(monkeypatch) -> None:
    monkeypatch.delenv("NERAJOB_FINDWORK_API_TOKEN", raising=False)
    monkeypatch.delenv("NERAJOB_FINDWORK_OFFLINE", raising=False)
    jobs = get_scraper("findwork").search("python", limit=10)
    assert jobs
    assert all(j.source == "findwork" for j in jobs)


def test_findwork_offline_explicit_env(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_FINDWORK_OFFLINE", "1")
    monkeypatch.setenv("NERAJOB_FINDWORK_API_TOKEN", "fake-token-ignored")
    jobs = get_scraper("findwork").search("python", limit=5)
    assert jobs
    assert all(j.source == "findwork" for j in jobs)


def test_findwork_offline_query_filter(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_FINDWORK_OFFLINE", "1")
    scraper = FindworkScraper()
    python_jobs = scraper.search("python", limit=10)
    rust_jobs = scraper.search("rust", limit=10)
    assert len(python_jobs) >= 1
    assert len(rust_jobs) == 0


def test_findwork_offline_location_filter(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_FINDWORK_OFFLINE", "1")
    scraper = FindworkScraper()
    eu_jobs = scraper.search("", location="EU", limit=10)
    assert len(eu_jobs) >= 1
    for j in eu_jobs:
        assert "eu" in j.location.lower() or "remote" in j.location.lower()


def test_findwork_offline_limit_enforced(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_FINDWORK_OFFLINE", "1")
    scraper = FindworkScraper()
    jobs = scraper.search("", limit=2)
    assert len(jobs) <= 2


def test_findwork_offline_deterministic(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_FINDWORK_OFFLINE", "1")
    scraper = FindworkScraper()
    run1 = scraper.search("python", limit=5)
    run2 = scraper.search("python", limit=5)
    assert len(run1) == len(run2)
    for a, b in zip(run1, run2):
        assert a.id == b.id
        assert a.title == b.title


def test_findwork_offline_returns_no_jobs_for_unknown_query(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_FINDWORK_OFFLINE", "1")
    scraper = FindworkScraper()
    jobs = scraper.search("cobol", limit=10)
    assert jobs == []


def test_findwork_offline_returns_all_when_no_query(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_FINDWORK_OFFLINE", "1")
    scraper = FindworkScraper()
    jobs = scraper.search("", limit=20)
    assert len(jobs) == 5


def test_findwork_offline_jobposting_fields(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_FINDWORK_OFFLINE", "1")
    scraper = FindworkScraper()
    jobs = scraper.search("python", limit=1)
    assert jobs
    j = jobs[0]
    assert j.id.startswith("findwork-")
    assert j.source == "findwork"
    assert j.title
    assert j.company
    assert j.location
    assert j.url
    assert j.description
    assert isinstance(j.tags, list)
    assert isinstance(j.remote, bool)


@pytest.fixture
def fake_findwork_api_response() -> dict:
    return {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": 12345,
                "role": "Senior Python Engineer",
                "company": {"name": "Findwork Live Co"},
                "location": "Remote (Worldwide)",
                "url": "https://findwork.dev/jobs/12345-senior-python-engineer/",
                "text": "Build scalable Python services. FastAPI + PostgreSQL. Remote-first.",
                "tags": ["python", "fastapi", "postgresql"],
                "keywords": ["backend", "api"],
                "remote": True,
            },
            {
                "id": 67890,
                "role": "DevOps Engineer",
                "company_name": "Cloudward Live",
                "location": "Remote (US)",
                "url": "https://findwork.dev/jobs/67890-devops-engineer/",
                "text": "Kubernetes, Terraform, AWS. On-call rotation every 6 weeks.",
                "tags": ["kubernetes", "terraform", "aws"],
                "keywords": ["devops", "sre"],
                "remote": True,
            },
        ],
    }


def test_findwork_live_api_parses_results(monkeypatch, fake_findwork_api_response) -> None:
    monkeypatch.setenv("NERAJOB_FINDWORK_API_TOKEN", "fake-token")
    monkeypatch.delenv("NERAJOB_FINDWORK_OFFLINE", raising=False)
    scraper = FindworkScraper()

    class FakeResponse:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return fake_findwork_api_response

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def get(self, url, params=None):
            assert "findwork.dev" in url
            return FakeResponse()

    monkeypatch.setattr("nerajob.scrapers.findwork.httpx.Client", FakeClient)

    jobs = scraper.search("python", limit=10)
    assert len(jobs) == 1
    assert all(j.source == "findwork" for j in jobs)
    assert jobs[0].title == "Senior Python Engineer"
    assert jobs[0].company == "Findwork Live Co"
    assert jobs[0].remote is True
    assert "python" in jobs[0].tags
    assert jobs[0].id == "findwork-12345"


def test_findwork_live_api_falls_back_on_error(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_FINDWORK_API_TOKEN", "fake-token")
    monkeypatch.delenv("NERAJOB_FINDWORK_OFFLINE", raising=False)
    scraper = FindworkScraper()

    class FailingClient:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def get(self, url, params=None):
            raise ConnectionError("simulated network failure")

    monkeypatch.setattr("nerajob.scrapers.findwork.httpx.Client", FailingClient)

    jobs = scraper.search("python", limit=5)
    assert jobs
    assert all(j.source == "findwork" for j in jobs)


def test_findwork_live_api_falls_back_on_403(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_FINDWORK_API_TOKEN", "revoked-token")
    monkeypatch.delenv("NERAJOB_FINDWORK_OFFLINE", raising=False)
    scraper = FindworkScraper()

    class ForbiddenResponse:
        status_code = 403
        def raise_for_status(self):
            import httpx
            raise httpx.HTTPStatusError(
                "403 Forbidden",
                request=httpx.Request("GET", "https://findwork.dev/api/jobs/"),
                response=httpx.Response(403),
            )
        def json(self): return {"detail": "Invalid token."}

    class ForbiddenClient:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def get(self, url, params=None): return ForbiddenResponse()

    monkeypatch.setattr("nerajob.scrapers.findwork.httpx.Client", ForbiddenClient)

    jobs = scraper.search("python", limit=5)
    assert jobs


def test_findwork_live_api_query_filter(monkeypatch, fake_findwork_api_response) -> None:
    monkeypatch.setenv("NERAJOB_FINDWORK_API_TOKEN", "fake-token")
    monkeypatch.delenv("NERAJOB_FINDWORK_OFFLINE", raising=False)
    scraper = FindworkScraper()

    class FakeResponse:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return fake_findwork_api_response

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def get(self, url, params=None): return FakeResponse()

    monkeypatch.setattr("nerajob.scrapers.findwork.httpx.Client", FakeClient)

    python_jobs = scraper.search("python", limit=10)
    assert len(python_jobs) == 1
    assert python_jobs[0].title == "Senior Python Engineer"

    kube_jobs = scraper.search("kubernetes", limit=10)
    assert len(kube_jobs) == 1
    assert kube_jobs[0].title == "DevOps Engineer"


def test_findwork_live_api_skips_items_without_title(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_FINDWORK_API_TOKEN", "fake-token")
    monkeypatch.delenv("NERAJOB_FINDWORK_OFFLINE", raising=False)
    scraper = FindworkScraper()

    payload = {
        "results": [
            {"id": 1, "role": "Valid Job", "company_name": "Co"},
            {"id": 2, "company_name": "No Title Co"},
            {"id": 3, "role": "", "company_name": "Empty Title Co"},
        ]
    }

    class FakeResponse:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return payload

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def get(self, url, params=None): return FakeResponse()

    monkeypatch.setattr("nerajob.scrapers.findwork.httpx.Client", FakeClient)

    jobs = scraper.search("", limit=10)
    assert len(jobs) == 1
    assert jobs[0].title == "Valid Job"


def test_findwork_company_fallback_to_unknown(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_FINDWORK_API_TOKEN", "fake-token")
    monkeypatch.delenv("NERAJOB_FINDWORK_OFFLINE", raising=False)
    scraper = FindworkScraper()

    payload = {
        "results": [
            {"id": 1, "role": "Mystery Job"},
        ]
    }

    class FakeResponse:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return payload

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def get(self, url, params=None): return FakeResponse()

    monkeypatch.setattr("nerajob.scrapers.findwork.httpx.Client", FakeClient)

    jobs = scraper.search("", limit=10)
    assert len(jobs) == 1
    assert jobs[0].company == "Unknown Company"


def test_findwork_offline_posting_has_correct_id_prefix(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_FINDWORK_OFFLINE", "1")
    scraper = FindworkScraper()
    jobs = scraper.search("python", limit=1)
    assert jobs[0].id.startswith("findwork-")


def test_findwork_offline_posting_remote_flag(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_FINDWORK_OFFLINE", "1")
    scraper = FindworkScraper()
    jobs = scraper.search("", limit=10)
    for j in jobs:
        assert j.remote is True
