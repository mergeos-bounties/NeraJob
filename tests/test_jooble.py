from unittest.mock import MagicMock, patch

import httpx

from nerajob.scrapers.registry import available_scrapers, get_scraper
from nerajob.scrapers.jooble import JoobleScraper


def test_jooble_registered() -> None:
    assert "jooble" in available_scrapers()


def test_jooble_no_api_key(monkeypatch) -> None:
    monkeypatch.delenv("NERAJOB_JOOBLE_API_KEY", raising=False)
    scraper = JoobleScraper()
    jobs = scraper.search("python")
    assert jobs == []


def _fake_client(json_data: dict) -> MagicMock:
    client = MagicMock()
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = json_data
    client.post.return_value = response
    return client


@patch("nerajob.scrapers.jooble.httpx.Client")
def test_jooble_parses_response(mock_client_class, monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_JOOBLE_API_KEY", "test-key")
    payload = {
        "totalCount": 2,
        "jobs": [
            {
                "id": "job-1",
                "title": "Python Developer",
                "company": "Tech Corp",
                "location": "Remote, US",
                "link": "https://jooble.org/job1",
                "snippet": "We need a Python developer.",
                "salary": "120k-150k",
            },
            {
                "id": "job-2",
                "title": "Backend Engineer",
                "company": "Startup Inc",
                "location": "New York, NY",
                "link": "https://jooble.org/job2",
                "snippet": "Backend role with Python.",
            },
        ],
    }
    mock_client_class.return_value.__enter__.return_value = _fake_client(payload)

    jobs = get_scraper("jooble").search("python", limit=10)
    assert len(jobs) == 2
    assert jobs[0].title == "Python Developer"
    assert jobs[0].company == "Tech Corp"
    assert jobs[0].location == "Remote, US"
    assert jobs[0].remote is True
    assert jobs[0].salary == "120k-150k"
    assert jobs[0].source == "jooble"
    assert jobs[1].title == "Backend Engineer"
    assert jobs[1].company == "Startup Inc"
    assert jobs[1].location == "New York, NY"
    assert jobs[1].remote is False


@patch("nerajob.scrapers.jooble.httpx.Client")
def test_jooble_with_location(mock_client_class, monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_JOOBLE_API_KEY", "test-key")
    payload = {"totalCount": 1, "jobs": [{"id": "l1", "title": "Engineer", "company": "Firm", "location": "Berlin"}]}
    mock_client_class.return_value.__enter__.return_value = _fake_client(payload)

    scraper = JoobleScraper()
    jobs = scraper.search("engineer", location="Berlin", limit=5)
    assert len(jobs) == 1
    assert jobs[0].location == "Berlin"


@patch("nerajob.scrapers.jooble.httpx.Client")
def test_jooble_network_error(mock_client_class, monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_JOOBLE_API_KEY", "test-key")
    client = MagicMock()
    client.post.side_effect = httpx.RequestError("connection failed")
    mock_client_class.return_value.__enter__.return_value = client

    jobs = get_scraper("jooble").search("python")
    assert jobs == []


@patch("nerajob.scrapers.jooble.httpx.Client")
def test_jooble_http_error(mock_client_class, monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_JOOBLE_API_KEY", "test-key")
    response = MagicMock()
    response.raise_for_status.side_effect = httpx.HTTPStatusError("403", request=MagicMock(), response=response)
    client = MagicMock()
    client.post.return_value = response
    mock_client_class.return_value.__enter__.return_value = client

    jobs = get_scraper("jooble").search("python")
    assert jobs == []


@patch("nerajob.scrapers.jooble.httpx.Client")
def test_jooble_bad_json(mock_client_class, monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_JOOBLE_API_KEY", "test-key")
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.side_effect = ValueError("bad json")
    client = MagicMock()
    client.post.return_value = response
    mock_client_class.return_value.__enter__.return_value = client

    jobs = get_scraper("jooble").search("python")
    assert jobs == []


@patch("nerajob.scrapers.jooble.httpx.Client")
def test_jooble_limit(mock_client_class, monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_JOOBLE_API_KEY", "test-key")
    payload = {
        "totalCount": 100,
        "jobs": [{"id": f"j{i}", "title": f"Job {i}", "company": "C"} for i in range(10)],
    }
    mock_client_class.return_value.__enter__.return_value = _fake_client(payload)

    jobs = get_scraper("jooble").search("python", limit=3)
    assert len(jobs) == 3
