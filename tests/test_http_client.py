from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest

from nerajob.http import (
    ScraperHTTPClient,
    _is_path_allowed,
    _parse_robots,
)


class TestTimeoutAndUserAgent:
    @pytest.mark.asyncio
    async def test_default_timeout_and_ua_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NERAJOB_HTTP_TIMEOUT", "15")
        monkeypatch.setenv("NERAJOB_USER_AGENT", "TestBot/1.0")
        client = ScraperHTTPClient()
        assert client.timeout == 15.0
        assert client.user_agent == "TestBot/1.0"
        await client.aclose()

    @pytest.mark.asyncio
    async def test_constructor_overrides_env(self) -> None:
        client = ScraperHTTPClient(timeout=42.0, ua="Custom/1.0")
        assert client.timeout == 42.0
        assert client.user_agent == "Custom/1.0"
        await client.aclose()


class TestRetryOn429:
    @pytest.mark.asyncio
    async def test_retry_on_429_then_success(self) -> None:
        responses = [
            httpx.Response(429, request=httpx.Request("GET", "http://example.com/")),
            httpx.Response(200, json={"ok": True}, request=httpx.Request("GET", "http://example.com/")),
        ]
        client = ScraperHTTPClient(timeout=5, max_retries=2, requests_per_second=100, respect_robots=False)

        mock_async = AsyncMock(spec=httpx.AsyncClient)
        mock_async.get = AsyncMock(side_effect=responses)

        async def mock_client() -> httpx.AsyncClient:
            return mock_async

        client._get_client = mock_client  # type: ignore[assignment]
        resp = await client.get("http://example.com/")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}
        await client.aclose()

    @pytest.mark.asyncio
    async def test_give_up_after_max_retries(self) -> None:
        responses = [
            httpx.Response(429, request=httpx.Request("GET", "http://example.com/")),
            httpx.Response(429, request=httpx.Request("GET", "http://example.com/")),
            httpx.Response(429, request=httpx.Request("GET", "http://example.com/")),
        ]
        client = ScraperHTTPClient(timeout=5, max_retries=2, requests_per_second=100, respect_robots=False)

        mock_async = AsyncMock(spec=httpx.AsyncClient)
        mock_async.get = AsyncMock(side_effect=responses)

        async def mock_client() -> httpx.AsyncClient:
            return mock_async

        client._get_client = mock_client  # type: ignore[assignment]
        with pytest.raises(httpx.HTTPStatusError):
            await client.get("http://example.com/")
        await client.aclose()


class TestRateLimiting:
    @pytest.mark.asyncio
    async def test_rate_limit_delays_requests(self) -> None:
        client = ScraperHTTPClient(timeout=5, requests_per_second=10.0, respect_robots=False)

        async def mock_client() -> httpx.AsyncClient:
            m = AsyncMock(spec=httpx.AsyncClient)
            m.get = AsyncMock(return_value=httpx.Response(200, request=httpx.Request("GET", "http://example.com/")))
            return m

        client._get_client = mock_client  # type: ignore[assignment]

        import time

        t0 = time.monotonic()
        await client.get("http://example.com/")
        await client.get("http://example.com/")
        elapsed = time.monotonic() - t0
        assert elapsed >= 0.09
        await client.aclose()

    @pytest.mark.asyncio
    async def test_rate_limit_separate_hosts(self) -> None:
        client = ScraperHTTPClient(timeout=5, requests_per_second=1.0)

        async def mock_client() -> httpx.AsyncClient:
            m = AsyncMock(spec=httpx.AsyncClient)
            m.get = AsyncMock(return_value=httpx.Response(200, request=httpx.Request("GET", "http://example.com/")))
            return m

        client._get_client = mock_client  # type: ignore[assignment]
        import time

        t0 = time.monotonic()
        await client.get("http://host-a.example/")
        await client.get("http://host-b.example/")
        elapsed = time.monotonic() - t0
        assert elapsed < 0.5
        await client.aclose()


class TestRobotsParsing:
    def test_parse_robots_basic(self) -> None:
        text = "User-agent: *\nDisallow: /private/\nAllow: /public/\n"
        rules = _parse_robots(text)
        assert ("user-agent", "*") in rules
        assert ("disallow", "/private/") in rules
        assert ("allow", "/public/") in rules

    def test_is_path_allowed_blocked(self) -> None:
        rules = [
            ("user-agent", "*"),
            ("disallow", "/private/"),
        ]
        assert _is_path_allowed("/private/admin", "NeraJob/0.1", rules) is False
        assert _is_path_allowed("/public", "NeraJob/0.1", rules) is True

    def test_is_path_allowed_allow_overrides(self) -> None:
        rules = [
            ("user-agent", "*"),
            ("disallow", "/"),
            ("allow", "/public/"),
        ]
        assert _is_path_allowed("/public/foo", "NeraJob/0.1", rules) is True
        assert _is_path_allowed("/private", "NeraJob/0.1", rules) is False

    @pytest.mark.asyncio
    async def test_robots_respected_in_get(self) -> None:
        robots_body = "User-agent: *\nDisallow: /\n"
        client = ScraperHTTPClient(timeout=5, respect_robots=True, max_retries=0)

        async def mock_client() -> httpx.AsyncClient:
            m = AsyncMock(spec=httpx.AsyncClient)
            m.get = AsyncMock(
                side_effect=lambda url, **kw: httpx.Response(
                    200,
                    text=robots_body if "robots.txt" in url else "OK",
                    request=httpx.Request("GET", url),
                )
            )
            return m

        client._get_client = mock_client  # type: ignore[assignment]
        with pytest.raises(httpx.HTTPStatusError, match="Blocked by robots"):
            await client.get("https://example.com/private")
        await client.aclose()
