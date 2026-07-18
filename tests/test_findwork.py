"""Tests for Findwork scraper (offline mode + mocked HTTP)."""
from __future__ import annotations

from unittest.mock import Mock, patch

from nerajob.scrapers.findwork import FindworkScraper


def test_findwork_offline_no_key() -> None:
    """Without NERAJOB_FINDWORK_KEY, should return offline samples."""
    import os

    if "NERAJOB_FINDWORK_KEY" in os.environ:
        del os.environ["NERAJOB_FINDWORK_KEY"]

    scraper = FindworkScraper()
    results = scraper.search("python", limit=5)
    assert len(results) >= 1
    assert all(r.source == "findwork" for r in results)


def test_findwork_offline_filtering() -> None:
    import os

    if "NERAJOB_FINDWORK_KEY" in os.environ:
        del os.environ["NERAJOB_FINDWORK_KEY"]

    scraper = FindworkScraper()
    results = scraper.search("sre", limit=5)
    assert len(results) >= 1
    assert any("Reliability" in r.title or "SRE" in r.title for r in results) or any("sre" in str(r.tags).lower() for r in results)


def test_findwork_offline_limit() -> None:
    import os

    if "NERAJOB_FINDWORK_KEY" in os.environ:
        del os.environ["NERAJOB_FINDWORK_KEY"]

    scraper = FindworkScraper()
    results = scraper.search("", limit=1)
    assert len(results) <= 1


def test_findwork_online_success() -> None:
    import os

    os.environ["NERAJOB_FINDWORK_KEY"] = "testkey123"
    try:
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "id": 789,
                    "role_name": "Python Developer",
                    "company_name": "Findwork Test",
                    "location": "Remote",
                    "text": "Develop Python applications",
                    "keywords": ["python", "django", "api"],
                    "url": "https://findwork.dev/jobs/789",
                }
            ]
        }

        with patch("nerajob.scrapers.findwork.httpx.Client") as mock_client:
            instance = Mock()
            instance.get.return_value = mock_response
            mock_client.return_value.__enter__.return_value = instance

            scraper = FindworkScraper()
            results = scraper.search("python", limit=5)
            assert len(results) == 1
            assert results[0].title == "Python Developer"
            assert results[0].source == "findwork"
    finally:
        del os.environ["NERAJOB_FINDWORK_KEY"]


def test_findwork_online_fallback_on_error() -> None:
    import os

    os.environ["NERAJOB_FINDWORK_KEY"] = "testkey123"
    try:
        with patch("nerajob.scrapers.findwork.httpx.Client") as mock_client:
            instance = Mock()
            instance.get.side_effect = Exception("Network error")
            mock_client.return_value.__enter__.return_value = instance

            scraper = FindworkScraper()
            results = scraper.search("python", limit=5)
            assert len(results) >= 1  # falls back to offline
    finally:
        del os.environ["NERAJOB_FINDWORK_KEY"]
