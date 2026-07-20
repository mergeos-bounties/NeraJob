from nerajob.scrapers.registry import available_scrapers, get_scraper


def test_arbeitnow_registered() -> None:
    assert "arbeitnow" in available_scrapers()


def test_arbeitnow_offline(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_ARBEITNOW_OFFLINE", "1")
    jobs = get_scraper("arbeitnow").search("python", limit=5)
    assert jobs
    assert all(j.source == "arbeitnow" for j in jobs)


def test_arbeitnow_online_mocked(monkeypatch) -> None:
    """Test the online path with a mocked HTTP response."""
    # Mock payload from Arbeitnow API
    mock_payload = {
        "data": [
            {
                "title": "Senior Python Engineer",
                "company_name": "Tech Corp",
                "location": "Berlin, Germany",
                "tags": ["python", "django", "remote"],
                "url": "https://www.arbeitnow.com/job/senior-python-engineer",
                "slug": "senior-python-engineer",
                "description": "We are looking for a senior Python engineer...",
            },
            {
                "title": "DevOps Engineer",
                "company_name": "Cloud Inc",
                "location": "Remote",
                "tags": ["aws", "docker", "kubernetes"],
                "url": "https://www.arbeitnow.com/job/devops-engineer",
                "slug": "devops-engineer",
                "description": "DevOps role with AWS and Kubernetes...",
            },
        ]
    }

    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self._json = json_data
            self.status_code = status_code

        def json(self):
            return self._json

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, url, *args, **kwargs):
            return MockResponse(mock_payload)

    # Patch httpx.Client to return our mock
    monkeypatch.setattr("httpx.Client", MockClient)
    # Ensure offline mode is not set
    monkeypatch.delenv("NERAJOB_ARBEITNOW_OFFLINE", raising=False)

    # With query="python", only the Python job should match
    jobs_python = get_scraper("arbeitnow").search("python", limit=5)
    assert len(jobs_python) == 1
    assert jobs_python[0].title == "Senior Python Engineer"
    assert jobs_python[0].company == "Tech Corp"
    assert jobs_python[0].location == "Berlin, Germany"
    assert "python" in jobs_python[0].tags

    # Without query, both jobs should be returned
    jobs_all = get_scraper("arbeitnow").search("", limit=5)
    assert len(jobs_all) == 2
    assert all(j.source == "arbeitnow" for j in jobs_all)
    assert jobs_all[1].title == "DevOps Engineer"
    assert jobs_all[1].company == "Cloud Inc"
    assert jobs_all[1].location == "Remote"
    assert "aws" in jobs_all[1].tags