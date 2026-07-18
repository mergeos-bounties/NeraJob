"""Tests for Adzuna scraper (offline mode + mocked HTTP)."""
from __future__ import annotations

from unittest.mock import Mock, patch

from nerajob.scrapers.adzuna import AdzunaScraper


def test_adzuna_offline_no_keys() -> None:
    """Without ADZUNA_APP_ID/KEY, should return offline samples."""
    import os

    os.environ.pop("ADZUNA_APP_ID", None)
    os.environ.pop("ADZUNA_APP_KEY", None)

    scraper = AdzunaScraper()
    results = scraper.search("python", limit=5)
    assert len(results) >= 1
    assert all(r.source == "adzuna" for r in results)


def test_adzuna_offline_filtering() -> None:
    import os

    os.environ.pop("ADZUNA_APP_ID", None)
    os.environ.pop("ADZUNA_APP_KEY", None)

    scraper = AdzunaScraper()
    results = scraper.search("data", limit=5)
    assert len(results) >= 1
    assert any("Data" in r.title for r in results)


def test_adzuna_offline_limit() -> None:
    import os

    os.environ.pop("ADZUNA_APP_ID", None)
    os.environ.pop("ADZUNA_APP_KEY", None)

    scraper = AdzunaScraper()
    results = scraper.search("", limit=2)
    assert len(results) <= 2


def test_adzuna_online_success() -> None:
    import os

    os.environ["ADZUNA_APP_ID"] = "testid"
    os.environ["ADZUNA_APP_KEY"] = "testkey"
    try:
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "abc123",
                    "title": "Senior Python Engineer",
                    "company": {"display_name": "Adzuna Test Co"},
                    "location": {"display_name": "London, UK"},
                    "description": "Build Python services",
                    "category": {"label": "Engineering / Software"},
                    "redirect_url": "https://www.adzuna.co.uk/jobs/abc123",
                    "salary_min": 80000,
                    "salary_max": 120000,
                    "salary_currency": "GBP",
                }
            ]
        }

        with patch("nerajob.scrapers.adzuna.httpx.Client") as mock_client:
            instance = Mock()
            instance.get.return_value = mock_response
            mock_client.return_value.__enter__.return_value = instance

            scraper = AdzunaScraper()
            results = scraper.search("python", limit=5)
            assert len(results) == 1
            assert results[0].title == "Senior Python Engineer"
            assert results[0].source == "adzuna"
            assert "80000" in results[0].salary
    finally:
        del os.environ["ADZUNA_APP_ID"]
        del os.environ["ADZUNA_APP_KEY"]


def test_adzuna_online_fallback_on_error() -> None:
    import os

    os.environ["ADZUNA_APP_ID"] = "testid"
    os.environ["ADZUNA_APP_KEY"] = "testkey"
    try:
        with patch("nerajob.scrapers.adzuna.httpx.Client") as mock_client:
            instance = Mock()
            instance.get.side_effect = Exception("Network error")
            mock_client.return_value.__enter__.return_value = instance

            scraper = AdzunaScraper()
            results = scraper.search("python", limit=5)
            assert len(results) >= 1  # falls back to offline
    finally:
        del os.environ["ADZUNA_APP_ID"]
        del os.environ["ADZUNA_APP_KEY"]
