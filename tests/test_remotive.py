from nerajob.scrapers.registry import available_scrapers, get_scraper


def test_remotive_registered() -> None:
    assert "remotive" in available_scrapers()


def test_remotive_offline(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_REMOTIVE_OFFLINE", "1")
    jobs = get_scraper("remotive").search("python", limit=5)
    assert len(jobs) >= 1
    assert all(j.source == "remotive" for j in jobs)
