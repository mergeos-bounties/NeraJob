from nerajob.scrapers.registry import available_scrapers, get_scraper


def test_themuse_registered() -> None:
    assert "themuse" in available_scrapers()


def test_themuse_offline(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_THEMUSE_OFFLINE", "1")
    jobs = get_scraper("themuse").search("python", limit=5)
    assert jobs
    assert all(j.source == "themuse" for j in jobs)
