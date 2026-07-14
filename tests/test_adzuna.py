"""Tests for Adzuna Jobs API scraper with mock HTTP responses."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from nerajob.scrapers.adzuna import AdzunaScraper, _COUNTRY_MAP


@pytest.fixture
def clear_env():
    keys = ["ADZUNA_APP_ID", "ADZUNA_APP_KEY", "NERAJOB_ADZUNA_COUNTRY"]
    saved = {k: os.environ.pop(k, None) for k in keys}
    yield
    for k, v in saved.items():
        if v is not None:
            os.environ[k] = v
        else:
            os.environ.pop(k, None)


class TestAdzunaCountryMapping:
    def test_supported_countries(self):
        assert "us" in _COUNTRY_MAP
        assert "gb" in _COUNTRY_MAP
        assert "de" in _COUNTRY_MAP
        assert "au" in _COUNTRY_MAP
        assert "in" in _COUNTRY_MAP

    def test_country_count(self):
        assert len(_COUNTRY_MAP) >= 40

    def test_normalize_country(self):
        assert AdzunaScraper._normalize_country("US") == "us"
        assert AdzunaScraper._normalize_country("  GB  ") == "gb"

    def test_unsupported_country_raises(self):
        with pytest.raises(ValueError, match="Unsupported country"):
            AdzunaScraper._normalize_country("zz")

    def test_default_country_is_us(self):
        scraper = AdzunaScraper()
        assert scraper.country == "us"


class TestAdzunaScraper:
    def test_name(self):
        assert AdzunaScraper().name == "adzuna"

    def test_no_credentials_returns_empty(self, clear_env):
        scraper = AdzunaScraper()
        result = scraper.search("python")
        assert result == []

    def test_no_credentials_logs_warning(self, clear_env, caplog):
        import logging
        caplog.set_level(logging.WARNING)
        scraper = AdzunaScraper()
        scraper.search("python")
        assert "ADZUNA_APP_ID" in caplog.text


class TestAdzunaMockAPI:
    @patch("nerajob.scrapers.adzuna.urlopen")
    def test_search_us(self, mock_urlopen, clear_env):
        os.environ["ADZUNA_APP_ID"] = "test_id"
        os.environ["ADZUNA_APP_KEY"] = "test_key"
        os.environ["NERAJOB_ADZUNA_COUNTRY"] = "us"

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "results": [
                {
                    "id": "12345",
                    "title": "Python Developer",
                    "company": {"display_name": "TechCorp"},
                    "location": {"display_name": "San Francisco"},
                    "description": "Build awesome Python apps",
                    "redirect_url": "https://example.com/job/1",
                    "salary_min": 120000,
                    "salary_max": 160000,
                    "salary_currency": "USD",
                    "contract_type": "permanent",
                    "created": "2026-07-10T10:00:00Z",
                },
                {
                    "id": "67890",
                    "title": "Senior Backend Engineer",
                    "company": {"display_name": "StartupX"},
                    "location": {"display_name": "Remote"},
                    "description": "Scalable systems",
                    "redirect_url": "https://example.com/job/2",
                    "salary_min": 140000,
                    "salary_max": 180000,
                    "salary_currency": "USD",
                    "contract_type": "permanent",
                    "created": "2026-07-09T10:00:00Z",
                },
            ]
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        scraper = AdzunaScraper(country="us")
        result = scraper.search("python", limit=20)

        assert len(result) == 2
        assert result[0].title == "Python Developer"
        assert result[0].company == "TechCorp"
        assert result[0].salary_min == 120000
        assert result[0].salary_currency == "USD"
        assert result[0].source == "adzuna"
        assert result[1].title == "Senior Backend Engineer"
        assert result[1].company == "StartupX"

    @patch("nerajob.scrapers.adzuna.urlopen")
    def test_search_gb(self, mock_urlopen, clear_env):
        os.environ["ADZUNA_APP_ID"] = "test_id"
        os.environ["ADZUNA_APP_KEY"] = "test_key"

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "results": [
                {
                    "id": "111",
                    "title": "Software Engineer",
                    "company": {"display_name": "London FinTech"},
                    "location": {"display_name": "London"},
                    "description": "FinTech platform",
                    "redirect_url": "https://example.com/job/3",
                    "salary_min": 50000,
                    "salary_max": 70000,
                    "salary_currency": "GBP",
                    "contract_type": "permanent",
                    "created": "2026-07-10T10:00:00Z",
                },
            ]
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        scraper = AdzunaScraper(country="gb")
        result = scraper.search("engineer", limit=20)

        assert len(result) == 1
        assert result[0].company == "London FinTech"
        assert result[0].salary_currency == "GBP"
        assert result[0].location == "London"
        assert "adzuna-gb" in result[0].id

    @patch("nerajob.scrapers.adzuna.urlopen")
    def test_search_de(self, mock_urlopen, clear_env):
        os.environ["ADZUNA_APP_ID"] = "test_id"
        os.environ["ADZUNA_APP_KEY"] = "test_key"

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "results": [
                {
                    "id": "222",
                    "title": "Entwickler",
                    "company": {"display_name": "BerlinTech"},
                    "location": {"display_name": "Berlin"},
                    "description": "Python Entwicklung",
                    "redirect_url": "https://example.com/job/4",
                    "salary_min": 60000,
                    "salary_max": 80000,
                    "salary_currency": "EUR",
                    "contract_type": "permanent",
                    "created": "2026-07-10T10:00:00Z",
                },
            ]
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        scraper = AdzunaScraper(country="de")
        result = scraper.search("python", limit=20)

        assert len(result) == 1
        assert result[0].salary_currency == "EUR"
        assert "adzuna-de" in result[0].id

    @patch("nerajob.scrapers.adzuna.urlopen")
    def test_search_empty_results(self, mock_urlopen, clear_env):
        os.environ["ADZUNA_APP_ID"] = "test_id"
        os.environ["ADZUNA_APP_KEY"] = "test_key"

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"results": []}).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        scraper = AdzunaScraper(country="us")
        result = scraper.search("nonexistent_job_xyz")

        assert result == []

    @patch("nerajob.scrapers.adzuna.urlopen")
    def test_api_error_graceful(self, mock_urlopen, clear_env):
        os.environ["ADZUNA_APP_ID"] = "test_id"
        os.environ["ADZUNA_APP_KEY"] = "test_key"

        mock_urlopen.side_effect = OSError("Connection refused")

        scraper = AdzunaScraper(country="us")
        result = scraper.search("python")

        assert result == []

    @patch("nerajob.scrapers.adzuna.urlopen")
    def test_results_capped_to_limit(self, mock_urlopen, clear_env):
        os.environ["ADZUNA_APP_ID"] = "test_id"
        os.environ["ADZUNA_APP_KEY"] = "test_key"

        jobs = [
            {
                "id": str(i),
                "title": f"Job {i}",
                "company": {"display_name": f"Company {i}"},
                "location": {"display_name": "Remote"},
                "description": "desc",
                "redirect_url": "https://example.com",
                "salary_min": 50000,
                "salary_max": 70000,
                "salary_currency": "USD",
                "contract_type": "permanent",
                "created": "2026-07-10T10:00:00Z",
            }
            for i in range(30)
        ]

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"results": jobs}).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        scraper = AdzunaScraper(country="us")
        result = scraper.search("test", limit=10)

        assert len(result) == 10

    @patch("nerajob.scrapers.adzuna.urlopen")
    def test_malformed_result_skipped(self, mock_urlopen, clear_env):
        os.environ["ADZUNA_APP_ID"] = "test_id"
        os.environ["ADZUNA_APP_KEY"] = "test_key"

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "results": [
                {"id": "1", "title": "Good", "company": {"display_name": "OK"},
                 "location": {"display_name": "Here"}, "description": "desc",
                 "redirect_url": "https://x.com", "created": "2026-07-10T10:00:00Z"},
                None,  # Malformed — should be skipped
                {"id": "3", "title": "Also Good", "company": {"display_name": "OK2"},
                 "location": {"display_name": "There"}, "description": "desc2",
                 "redirect_url": "https://y.com", "created": "2026-07-10T10:00:00Z"},
            ]
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        scraper = AdzunaScraper(country="us")
        result = scraper.search("test")

        assert len(result) == 2
        assert result[0].title == "Good"
        assert result[1].title == "Also Good"

    @patch("nerajob.scrapers.adzuna.urlopen")
    def test_url_includes_country(self, mock_urlopen, clear_env):
        os.environ["ADZUNA_APP_ID"] = "test_id"
        os.environ["ADZUNA_APP_KEY"] = "test_key"

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"results": []}).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        scraper = AdzunaScraper(country="au")
        scraper.search("python", limit=5)

        # Verify URL includes country code
        call_url = mock_urlopen.call_args[0][0].full_url if hasattr(mock_urlopen.call_args[0][0], 'full_url') else str(mock_urlopen.call_args[0][0])
        assert "/au/" in call_url or "au/" in str(mock_urlopen.call_args)


class TestBuildUrl:
    def test_build_url_structure(self):
        scraper = AdzunaScraper(country="us")
        scraper._app_id = "myapp"
        scraper._app_key = "mykey"
        url = scraper._build_url("python developer", "San Francisco", page=1)
        assert "api.adzuna.com" in url
        assert "/us/" in url
        assert "app_id=myapp" in url
        assert "app_key=mykey" in url
        assert "python%20developer" in url.lower() or "python+developer" in url

    def test_build_url_no_location(self):
        scraper = AdzunaScraper(country="gb")
        scraper._app_id = "app"
        scraper._app_key = "key"
        url = scraper._build_url("engineer", "", page=2)
        assert "/gb/" in url
        assert "page=2" in url or "/2?" in url
