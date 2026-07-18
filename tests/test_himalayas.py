"""Tests for Himalayas scraper (offline mode + mocked HTTP)."""
from __future__ import annotations

from unittest.mock import Mock, patch

from nerajob.scrapers.himalayas import HimalayasScraper


def test_himalayas_offline_mode() -> None:
    import os

    os.environ["NERAJOB_HIMALAYAS_OFFLINE"] = "1"
    try:
        scraper = HimalayasScraper()
        results = scraper.search("python", limit=5)
        assert len(results) >= 1
        assert all(r.source == "himalayas" for r in results)
    finally:
        del os.environ["NERAJOB_HIMALAYAS_OFFLINE"]


def test_himalayas_offline_filtering() -> None:
    import os

    os.environ["NERAJOB_HIMALAYAS_OFFLINE"] = "1"
    try:
        scraper = HimalayasScraper()
        results = scraper.search("devops", limit=5)
        assert len(results) >= 1
        assert any("DevOps" in r.title for r in results)
    finally:
        del os.environ["NERAJOB_HIMALAYAS_OFFLINE"]


def test_himalayas_offline_limit() -> None:
    import os

    os.environ["NERAJOB_HIMALAYAS_OFFLINE"] = "1"
    try:
        scraper = HimalayasScraper()
        results = scraper.search("", limit=2)
        assert len(results) <= 2
    finally:
        del os.environ["NERAJOB_HIMALAYAS_OFFLINE"]


def test_himalayas_offline_empty_query() -> None:
    import os

    os.environ["NERAJOB_HIMALAYAS_OFFLINE"] = "1"
    try:
        scraper = HimalayasScraper()
        results = scraper.search("", limit=5)
        assert len(results) >= 1
    finally:
        del os.environ["NERAJOB_HIMALAYAS_OFFLINE"]


def test_himalayas_online_success() -> None:
    import os

    if "NERAJOB_HIMALAYAS_OFFLINE" in os.environ:
        del os.environ["NERAJOB_HIMALAYAS_OFFLINE"]

    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = {
        "jobs": [
            {
                "id": "123",
                "title": "Python Engineer",
                "company": {"name": "Himalayas Test"},
                "location": "Remote",
                "description": "Build APIs with Python",
                "categories": ["engineering", "backend"],
                "url": "https://himalayas.app/jobs/123",
            }
        ]
    }

    with patch("nerajob.scrapers.himalayas.httpx.Client") as mock_client:
        instance = Mock()
        instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = instance

        scraper = HimalayasScraper()
        results = scraper.search("python", limit=5)
        assert len(results) == 1
        assert results[0].title == "Python Engineer"
        assert results[0].source == "himalayas"


def test_himalayas_online_fallback_on_error() -> None:
    import os

    if "NERAJOB_HIMALAYAS_OFFLINE" in os.environ:
        del os.environ["NERAJOB_HIMALAYAS_OFFLINE"]

    with patch("nerajob.scrapers.himalayas.httpx.Client") as mock_client:
        instance = Mock()
        instance.get.side_effect = Exception("Network error")
        mock_client.return_value.__enter__.return_value = instance

        scraper = HimalayasScraper()
        results = scraper.search("python", limit=5)
        assert len(results) >= 1  # falls back to offline
