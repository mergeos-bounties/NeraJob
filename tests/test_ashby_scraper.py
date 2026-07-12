"""Tests for the Ashby scraper."""

from nerajob.scrapers.ashby import AshbyScraper


def test_ashby_scraper_filters_python_roles():
    jobs = AshbyScraper().search(query="python", location="remote", limit=10)
    assert jobs
    for j in jobs:
        assert "python" in f"{j.title} {j.company} {j.description} {' '.join(j.tags)}".lower()


def test_ashby_scraper_filters_by_location():
    jobs = AshbyScraper().search(query="", location="san francisco", limit=10)
    assert all("san francisco" in j.location.lower() for j in jobs)


def test_ashby_scraper_respects_limit():
    jobs = AshbyScraper().search(query="", limit=1)
    assert len(jobs) <= 1


def test_ashby_scraper_ids_stable():
    a = AshbyScraper().search(query="python", limit=5)
    b = AshbyScraper().search(query="python", limit=5)
    assert [j.id for j in a] == [j.id for j in b]


def test_ashby_scraper_empty_board_id_returns_sample():
    jobs = AshbyScraper().search(query="", limit=10)
    assert jobs
    assert jobs[0].source == "ashby"


def test_ashby_scraper_no_match_returns_empty():
    jobs = AshbyScraper().search(query="zzzznotexistkeyword", limit=10)
    assert jobs == []
