"""Tests for TopCV Vietnam jobs scraper."""

from nerajob.scrapers.registry import available_scrapers, get_scraper


def test_topcv_registered() -> None:
    assert "topcv" in available_scrapers()


def test_topcv_offline(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_TOPCV_OFFLINE", "1")
    jobs = get_scraper("topcv").search("python", limit=5)
    assert jobs
    assert all(j.source == "topcv" for j in jobs)


def test_topcv_offline_with_location(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_TOPCV_OFFLINE", "1")
    jobs = get_scraper("topcv").search("engineer", location="ho chi minh", limit=5)
    assert jobs
    assert all(j.source == "topcv" for j in jobs)


def test_topcv_offline_no_query(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_TOPCV_OFFLINE", "1")
    jobs = get_scraper("topcv").search("", limit=5)
    assert jobs
    assert all(j.source == "topcv" for j in jobs)


def test_topcv_offline_kubernetes(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_TOPCV_OFFLINE", "1")
    jobs = get_scraper("topcv").search("kubernetes", limit=5)
    assert jobs
    # Should return the DevOps job
    titles = [j.title.lower() for j in jobs]
    assert any("devops" in t for t in titles)


def test_topcv_offline_limit(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_TOPCV_OFFLINE", "1")
    jobs = get_scraper("topcv").search("engineer", limit=2)
    assert len(jobs) <= 2
    assert all(j.source == "topcv" for j in jobs)