"""Tests for USAJOBS official API scraper adapter.

Run with: pytest tests/test_usajobs.py

These tests use offline/sample mode (no network needed).
Bounty: https://github.com/mergeos-bounties/NeraJob/issues/8
"""

from __future__ import annotations

from nerajob.scrapers.registry import available_scrapers, get_scraper


def test_usajobs_registered() -> None:
    """Scraper should be registered under name 'usajobs'."""
    scrapers = available_scrapers()
    assert "usajobs" in scrapers
    scraper = get_scraper("usajobs")
    assert scraper.name == "usajobs"


def test_usajobs_offline(monkeypatch) -> None:
    """Offline mode returns sample job postings."""
    monkeypatch.setenv("NERAJOB_USAJOBS_OFFLINE", "1")
    jobs = get_scraper("usajobs").search(query="specialist", limit=5)
    assert len(jobs) > 0, "Should return at least one sample job"
    assert all(j.source == "usajobs" for j in jobs), "All jobs should have source='usajobs'"


def test_usajobs_offline_no_query(monkeypatch) -> None:
    """Offline mode returns all samples when no query given."""
    monkeypatch.setenv("NERAJOB_USAJOBS_OFFLINE", "1")
    jobs = get_scraper("usajobs").search(query="", limit=20)
    assert len(jobs) >= 3, "Should return all offline samples"


def test_usajobs_offline_query_filter(monkeypatch) -> None:
    """Offline mode should filter by query."""
    monkeypatch.setenv("NERAJOB_USAJOBS_OFFLINE", "1")
    jobs = get_scraper("usajobs").search(query="nurse", limit=20)
    assert len(jobs) >= 1, "Should find nurse-related job"
    titles = [j.title for j in jobs]
    assert any("nurse" in t.lower() for t in titles)


def test_usajobs_offline_location_filter(monkeypatch) -> None:
    """Offline mode filters by location."""
    monkeypatch.setenv("NERAJOB_USAJOBS_OFFLINE", "1")
    jobs = get_scraper("usajobs").search(query="", location="Portland", limit=20)
    assert len(jobs) >= 1, "Should find Portland-located job"
    locations = [j.location.lower() for j in jobs]
    assert any("portland" in loc for loc in locations)


def test_usajobs_offline_limit(monkeypatch) -> None:
    """Offline mode respects the limit parameter."""
    monkeypatch.setenv("NERAJOB_USAJOBS_OFFLINE", "1")
    jobs = get_scraper("usajobs").search(query="", limit=2)
    assert len(jobs) <= 2, "Should return at most 2 jobs"


def test_usajobs_fallback_when_no_key(monkeypatch) -> None:
    """When NERAJOB_USAJOBS_API_KEY is not set, should fall back to offline."""
    # Ensure key env var is removed
    monkeypatch.delenv("NERAJOB_USAJOBS_API_KEY", raising=False)
    jobs = get_scraper("usajobs").search(query="specialist", limit=3)
    assert len(jobs) > 0, "Should fall back to offline mode"
