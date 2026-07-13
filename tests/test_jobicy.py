from nerajob.scrapers import jobicy
from nerajob.scrapers.registry import available_scrapers, get_scraper


def test_jobicy_registered() -> None:
    assert "jobicy" in available_scrapers()


def test_jobicy_offline(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_JOBICY_OFFLINE", "1")
    jobs = get_scraper("jobicy").search("python", limit=5)
    assert jobs
    assert all(j.source == "jobicy" for j in jobs)


def test_jobicy_http_mapping(monkeypatch) -> None:
    seen: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "jobs": [
                    {
                        "id": 149156,
                        "url": "https://jobicy.com/jobs/149156-python-react",
                        "jobSlug": "149156-python-react",
                        "jobTitle": "Senior Full-stack Engineer (Python/React)",
                        "companyName": "Truelogic",
                        "jobIndustry": ["Software Engineering"],
                        "jobType": ["Full-Time"],
                        "jobGeo": "LATAM",
                        "jobLevel": "Senior",
                        "jobDescription": "<p>Build Python and React applications.</p>",
                        "annualSalaryMin": "85000",
                        "annualSalaryMax": "95000",
                        "salaryCurrency": "USD",
                    }
                ]
            }

    class FakeClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            return None

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def get(self, url: str, params: dict[str, object]) -> FakeResponse:
            seen["url"] = url
            seen["params"] = params
            return FakeResponse()

    monkeypatch.setattr(jobicy.httpx, "Client", FakeClient)

    jobs = get_scraper("jobicy").search("python", location="latam", limit=3)

    assert seen["url"] == "https://jobicy.com/api/v2/remote-jobs"
    assert seen["params"] == {"count": 3, "tag": "python", "geo": "latam"}
    assert len(jobs) == 1
    assert jobs[0].id.startswith("jobicy-")
    assert jobs[0].company == "Truelogic"
    assert jobs[0].location == "LATAM"
    assert jobs[0].salary == "85000-95000 USD"
    assert "python" in jobs[0].description.lower()
