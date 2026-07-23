from nerajob.scrapers.registry import available_scrapers, get_scraper


def test_himalayas_registered() -> None:
    assert "himalayas" in available_scrapers()


def test_himalayas_offline(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_HIMALAYAS_OFFLINE", "1")
    jobs = get_scraper("himalayas").search("python", limit=5)
    assert len(jobs) >= 1
    assert all(j.source == "himalayas" for j in jobs)