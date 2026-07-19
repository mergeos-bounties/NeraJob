from nerajob.scrapers.registry import available_scrapers, get_scraper


def test_himalayas_registered() -> None:
    assert "himalayas" in available_scrapers()


def test_himalayas_offline(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_HIMALAYAS_OFFLINE", "1")
    jobs = get_scraper("himalayas").search("go", limit=5)
    assert jobs
    assert all(j.source == "himalayas" for j in jobs)


def test_himalayas_offline_frontend(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_HIMALAYAS_OFFLINE", "1")
    jobs = get_scraper("himalayas").search("frontend", limit=5)
    assert jobs
    assert any("frontend" in j.title.lower() for j in jobs)