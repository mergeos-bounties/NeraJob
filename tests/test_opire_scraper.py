"""Tests for the Opire scraper."""
from unittest.mock import MagicMock

import pytest

from nerajob.scrapers.opire import OpireScraper


def _item(
    title: str = "Add Wayland support",
    org_name: str = "autokey",
    url: str = "https://github.com/autokey/autokey/issues/87",
    languages: list[str] | None = None,
    bounty_cents: int = 59000,
) -> dict:
    return {
        "id": "test-id",
        "title": title,
        "url": url,
        "platform": "GitHub",
        "featuredBy": None,
        "claimerUsers": [],
        "tryingUsers": [],
        "programmingLanguages": languages or ["Python"],
        "createdAt": 1700000000000,
        "pendingPrice": {"value": bounty_cents, "unit": "USD_CENT"},
        "organization": {
            "id": "org-id",
            "logoURL": "https://avatars.githubusercontent.com/u/123?v=4",
            "url": f"https://github.com/{org_name}",
            "name": org_name,
        },
        "project": {
            "id": "proj-id",
            "url": f"https://github.com/{org_name}/some-repo",
            "name": "some-repo",
            "isPublic": True,
            "isBotInstalled": False,
        },
    }


class TestOpireScraper:
    def test_parse_basic(self):
        scraper = OpireScraper()
        posting = scraper._parse(_item())
        assert posting is not None
        assert posting.title == "Add Wayland support"
        assert posting.company == "autokey"
        assert posting.source == "opire"
        assert posting.remote is True
        assert posting.salary == "$590"
        assert "Python" in posting.tags
        assert posting.url == "https://github.com/autokey/autokey/issues/87"

    def test_parse_no_url(self):
        scraper = OpireScraper()
        posting = scraper._parse(_item(url=""))
        assert posting is None

    def test_parse_non_github_url(self):
        scraper = OpireScraper()
        posting = scraper._parse(_item(url="https://gitlab.com/foo/bar/issues/1"))
        assert posting is None

    def test_parse_zero_bounty(self):
        scraper = OpireScraper()
        posting = scraper._parse(_item(bounty_cents=0))
        assert posting is not None
        assert posting.salary == ""  # $0 returns empty string, bounty_str only if > 0

    def test_parse_large_bounty(self):
        scraper = OpireScraper()
        posting = scraper._parse(_item(bounty_cents=1_515_000))
        assert posting is not None
        assert posting.salary == "$15150"

    def test_parse_fallback_title(self):
        scraper = OpireScraper()
        posting = scraper._parse(_item(title="", url="https://github.com/foo/bar/issues/42"))
        assert posting is not None
        assert posting.title == "Issue #42"

    def test_search_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """search returns empty on network error."""
        scraper = OpireScraper()

        class FakeResp:
            raise_for_status = MagicMock()
            json = MagicMock(return_value=[])

        class FakeClient:
            def __init__(self, **kwargs: object) -> None:
                pass

            def __enter__(self) -> "FakeClient":
                return self

            def __exit__(self, *args: object) -> None:
                pass

            def get(self, url: str, **kwargs: object) -> FakeResp:
                return FakeResp()

        import nerajob.scrapers.opire as opire_mod

        monkeypatch.setattr(opire_mod.httpx, "Client", FakeClient)
        result = scraper.search("")
        assert result == []