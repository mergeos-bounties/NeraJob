"""
Tests for Adzuna Jobs API scraper.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from src.nerajob.scrapers.adzuna import AdzunaScraper


@pytest.fixture
def mock_env():
    """Mock environment variables."""
    with patch.dict(os.environ, {"ADZUNA_APP_ID": "test_id", "ADZUNA_APP_KEY": "test_key"}):
        yield


def test_init_missing_keys():
    """Test that missing environment variables raise an error."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="ADZUNA_APP_ID and ADZUNA_APP_KEY"):
            AdzunaScraper()


def test_init_success(mock_env):
    """Test successful initialization."""
    scraper = AdzunaScraper()
    assert scraper.app_id == "test_id"
    assert scraper.app_key == "test_key"
    assert scraper.SOURCE_NAME == "adzuna"


@patch("src.nerajob.scrapers.adzuna.requests.get")
def test_search_success(mock_get, mock_env):
    """Test successful search with mocked API response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {
                "id": "12345",
                "title": "Python Developer",
                "company": {"display_name": "Tech Corp"},
                "location": {"display_name": "Remote"},
                "description": "Python development role",
                "redirect_url": "https://adzuna.com/job/12345",
                "salary_min": 80000,
                "salary_max": 120000,
                "created": "2024-01-15T10:00:00Z"
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    scraper = AdzunaScraper()
    results = scraper.search("python", "us", limit=1)

    assert len(results) == 1
    assert results[0].title == "Python Developer"
    assert results[0].company == "Tech Corp"
    assert "80000" in results[0].salary
    assert results[0].source == "adzuna"


@patch("src.nerajob.scrapers.adzuna.requests.get")
def test_search_network_error(mock_get, mock_env):
    """Test graceful degradation on network errors."""
    mock_get.side_effect = Exception("Network error")

    scraper = AdzunaScraper()
    results = scraper.search("python", "us")

    assert results == []


@patch("src.nerajob.scrapers.adzuna.requests.get")
def test_search_empty_results(mock_get, mock_env):
    """Test handling of empty search results."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    scraper = AdzunaScraper()
    results = scraper.search("nonexistent_keyword_xyz", "us")

    assert results == []


@patch("src.nerajob.scrapers.adzuna.requests.get")
def test_search_different_countries(mock_get, mock_env):
    """Test that country parameter is passed correctly."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    scraper = AdzunaScraper()

    # Test US
    scraper.search("python", "us")
    call_args = mock_get.call_args[0][0]
    assert "/us/search/" in call_args

    # Test GB
    mock_get.reset_mock()
    scraper.search("python", "gb")
    call_args = mock_get.call_args[0][0]
    assert "/gb/search/" in call_args


def test_get_country_options(mock_env):
    """Test supported country options."""
    scraper = AdzunaScraper()
    countries = scraper.get_country_options()
    assert "us" in countries
    assert "gb" in countries
    assert "de" in countries
    assert len(countries) > 10