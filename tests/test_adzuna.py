"""Tests for Adzuna Jobs API scraper adapter.

Run with: pytest tests/test_adzuna.py

These tests use offline/sample mode (no network needed).
Bounty: https://github.com/mergeos-bounties/NeraJob/issues/7
"""

from __future__ import annotations

from nerajob.scrapers.registry import available_scrapers, get_scraper


def test_adzuna_registered() -> None:
    """Scraper should be registered under name 'adzuna'."""
    scrapers = available_scrapers()
    assert "adzuna" in scrapers
    scraper = get_scraper("adzuna")
    assert scraper.name == "adzuna"


def test_adzuna_offline(monkeypatch) -> None:
    """Offline mode returns sample job postings."""
    monkeypatch.setenv("NERAJOB_ADZUNA_OFFLINE", "1")
    jobs = get_scraper("adzuna").search(query="python", limit=5)
    assert len(jobs) > 0, "Should return at least one sample job"
    assert all(j.source == "adzuna" for j in jobs), "All jobs should have source='adzuna'"


def test_adzuna_offline_no_query(monkeypatch) -> None:
    """Offline mode returns all samples when no query given."""
    monkeypatch.setenv("NERAJOB_ADZUNA_OFFLINE", "1")
    jobs = get_scraper("adzuna").search(query="", limit=20)
    assert len(jobs) >= 3, "Should return all offline samples"


def test_adzuna_offline_query_filter(monkeypatch) -> None:
    """Offline mode should filter by query."""
    monkeypatch.setenv("NERAJOB_ADZUNA_OFFLINE", "1")
    jobs = get_scraper("adzuna").search(query="frontend", limit=20)
    assert len(jobs) >= 1, "Should find Frontend-related job"
    titles = [j.title for j in jobs]
    assert any("frontend" in t.lower() for t in titles)


def test_adzuna_offline_location_filter(monkeypatch) -> None:
    """Offline mode filters by location context."""
    monkeypatch.setenv("NERAJOB_ADZUNA_OFFLINE", "1")
    jobs = get_scraper("adzuna").search(query="", location="Berlin", limit=20)
    assert len(jobs) >= 1, "Should find Berlin-located job"
    locations = [j.location.lower() for j in jobs]
    assert any("berlin" in loc for loc in locations)


def test_adzuna_offline_limit(monkeypatch) -> None:
    """Offline mode respects the limit parameter."""
    monkeypatch.setenv("NERAJOB_ADZUNA_OFFLINE", "1")
    jobs = get_scraper("adzuna").search(query="", limit=2)
    assert len(jobs) <= 2, "Should return at most 2 jobs"


def test_adzuna_fallback_when_no_creds() -> None:
    """When ADZUNA_APP_ID/KEY are not set, should fall back to offline."""
    # Ensure env vars are not set
    import os
    if "ADZUNA_APP_ID" in os.environ:
        del os.environ["ADZUNA_APP_ID"]
    if "ADZUNA_APP_KEY" in os.environ:
        del os.environ["ADZUNA_APP_KEY"]
    jobs = get_scraper("adzuna").search(query="python", limit=3)
    assert len(jobs) > 0, "Should fall back to offline mode"
