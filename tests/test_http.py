"""Tests for nerajob.http — shared HTTP client with rate limiting, retries, and robots.txt."""

from __future__ import annotations

import time

import httpx
import pytest

from nerajob.http import (
    RateLimiter,
    RobotsChecker,
    RateLimitedTransport,
    create_client,
)


class TestRateLimiter:
    def test_no_wait_first_request(self):
        rl = RateLimiter(min_delay=1.0)
        waited = rl.wait_if_needed("example.com")
        assert waited == 0.0

    def test_waits_for_second_fast_request(self):
        rl = RateLimiter(min_delay=0.5)
        rl.wait_if_needed("example.com")
        time.sleep(0.1)
        waited = rl.wait_if_needed("example.com")
        # Should have waited at least (0.5 - 0.1) = 0.4
        assert waited >= 0.39

    def test_separate_hosts_dont_wait(self):
        rl = RateLimiter(min_delay=1.0)
        rl.wait_if_needed("host-a.com")
        waited = rl.wait_if_needed("host-b.com")
        assert waited == 0.0

    def test_reset_clears_state(self):
        rl = RateLimiter(min_delay=1.0)
        rl.wait_if_needed("example.com")
        rl.reset()
        waited = rl.wait_if_needed("example.com")
        assert waited == 0.0


class TestRobotsChecker:
    def test_no_host_returns_allowed(self):
        rc = RobotsChecker()
        assert rc.is_allowed("/local/file")

    def test_cached_result(self):
        rc = RobotsChecker()
        host = "localhost"
        # Pre-seed cache with a parsed result that blocks everything
        from urllib.robotparser import RobotFileParser
        rp = RobotFileParser()
        rp.parse(["User-agent: *", "Disallow: /"].copy())
        rc._cache[host] = rp
        rc._ttl[host] = time.monotonic()
        assert rc.is_allowed("https://localhost/secret") is False

    def test_unknown_host_allows(self):
        rc = RobotsChecker()
        # Host not in cache, we won't actually fetch
        rc._cache["unknown.example.com"] = None
        assert rc.is_allowed("https://unknown.example.com/page") is True


class TestRateLimitedTransport:
    def test_handles_request_once(self):
        transport = RateLimitedTransport(max_retries=0)
        request = httpx.Request("GET", "https://example.com/")
        try:
            response = transport.handle_request(request)
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("No network available")

    def test_retry_on_503(self, monkeypatch):
        """Test that the transport retries on 503 server errors."""
        transport = RateLimitedTransport(max_retries=2, backoff_factor=0.01)
        call_count = [0]

        def fake_handle(request):
            call_count[0] += 1
            if call_count[0] < 2:
                return httpx.Response(503, request=request)
            return httpx.Response(200, request=request, json={"ok": True})

        monkeypatch.setattr(transport._transport, "handle_request", fake_handle)
        request = httpx.Request("GET", "https://example.com/")
        response = transport.handle_request(request)
        assert response.status_code == 200
        assert call_count[0] == 2

    def test_retry_on_429(self, monkeypatch):
        """Test that the transport retries on 429 rate limit errors."""
        transport = RateLimitedTransport(max_retries=3, backoff_factor=0.01)
        call_count = [0]

        def fake_handle(request):
            call_count[0] += 1
            if call_count[0] < 3:
                resp = httpx.Response(429, request=request)
                resp.headers["Retry-After"] = "0.001"
                return resp
            return httpx.Response(200, request=request, json={"ok": True})

        monkeypatch.setattr(transport._transport, "handle_request", fake_handle)
        request = httpx.Request("GET", "https://example.com/")
        response = transport.handle_request(request)
        assert response.status_code == 200
        assert call_count[0] == 3

    def test_max_retries_exceeded_raises(self, monkeypatch):
        """Test that exceeding max retries raises an error."""
        transport = RateLimitedTransport(max_retries=1, backoff_factor=0.01)

        def fake_handle(request):
            return httpx.Response(503, request=request)

        monkeypatch.setattr(transport._transport, "handle_request", fake_handle)
        request = httpx.Request("GET", "https://example.com/")
        with pytest.raises(httpx.RequestError):
            transport.handle_request(request)


class TestCreateClient:
    def test_returns_httpx_client(self):
        client = create_client()
        assert isinstance(client, httpx.Client)
        assert "User-Agent" in client.headers
        client.close()

    def test_custom_timeout(self):
        client = create_client(timeout=5.0)
        assert client.timeout == httpx.Timeout(5.0)
        client.close()

    def test_custom_user_agent(self):
        client = create_client(user_agent="TestBot/1.0")
        assert client.headers["User-Agent"] == "TestBot/1.0"
        client.close()