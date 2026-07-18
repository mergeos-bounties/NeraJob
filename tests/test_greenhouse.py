"""Tests for Greenhouse scraper (offline mode + mocked HTTP)."""
from __future__ import annotations

from unittest.mock import Mock, patch

from nerajob.scrapers.greenhouse import GreenhouseScraper


def test_greenhouse_offline_no_board_env() -> None:
    """Without NERAJOB_GREENHOUSE_BOARD, should return offline samples."""
    import os

    if "NERAJOB_GREENHOUSE_BOARD" in os.environ:
        del os.environ["NERAJOB_GREENHOUSE_BOARD"]

    scraper = GreenhouseScraper()
    results = scraper.search("engineer", limit=5)
    assert len(results) >= 1
    assert all(r.source == "greenhouse" for r in results)


def test_greenhouse_offline_filtering() -> None:
    import os

    if "NERAJOB_GREENHOUSE_BOARD" in os.environ:
        del os.environ["NERAJOB_GREENHOUSE_BOARD"]

    scraper = GreenhouseScraper()
    results = scraper.search("data", limit=5)
    assert len(results) >= 1
    assert any("Data" in r.title for r in results)


def test_greenhouse_offline_limit() -> None:
    import os

    if "NERAJOB_GREENHOUSE_BOARD" in os.environ:
        del os.environ["NERAJOB_GREENHOUSE_BOARD"]

    scraper = GreenhouseScraper()
    results = scraper.search("", limit=2)
    assert len(results) <= 2


def test_greenhouse_online_success() -> None:
    import os

    os.environ["NERAJOB_GREENHOUSE_BOARD"] = "testcompany"
    try:
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "jobs": [
                {
                    "id": 456,
                    "title": "Backend Engineer",
                    "location": {"name": "San Francisco, CA"},
                    "absolute_url": "https://boards.greenhouse.io/testcompany/jobs/456",
                    "content": "<p>Build backend services.</p>",
                    "departments": [{"id": 1, "name": "Engineering"}],
                    "offices": [{"id": 1, "name": "HQ", "location": "SF"}],
                }
            ]
        }

        with patch("nerajob.scrapers.greenhouse.httpx.Client") as mock_client:
            instance = Mock()
            instance.get.return_value = mock_response
            mock_client.return_value.__enter__.return_value = instance

            scraper = GreenhouseScraper()
            results = scraper.search("backend", limit=5)
            assert len(results) == 1
            assert results[0].title == "Backend Engineer"
            assert results[0].source == "greenhouse"
            assert results[0].company == "Engineering"
    finally:
        del os.environ["NERAJOB_GREENHOUSE_BOARD"]


def test_greenhouse_online_fallback_on_error() -> None:
    import os

    os.environ["NERAJOB_GREENHOUSE_BOARD"] = "testcompany"
    try:
        with patch("nerajob.scrapers.greenhouse.httpx.Client") as mock_client:
            instance = Mock()
            instance.get.side_effect = Exception("Network error")
            mock_client.return_value.__enter__.return_value = instance

            scraper = GreenhouseScraper()
            results = scraper.search("engineer", limit=5)
            assert len(results) >= 1  # falls back to offline
    finally:
        del os.environ["NERAJOB_GREENHOUSE_BOARD"]
