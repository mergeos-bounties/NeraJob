"""Shared HTTP client with rate limiting, retries, and robots.txt awareness.

Usage:
    from nerajob.http import create_client
    client = create_client()
    response = client.get("https://remoteok.com/api")
"""

from __future__ import annotations

import os
import time
from urllib.parse import urlparse

import httpx
from urllib.robotparser import RobotFileParser


class RateLimiter:
    """Per-host rate limiter ensuring minimum delay between requests."""

    def __init__(self, min_delay: float = 1.0):
        self._min_delay = min_delay
        self._last_request: dict[str, float] = {}

    def wait_if_needed(self, host: str) -> float:
        """Wait if needed for the given host. Returns seconds waited."""
        now = time.monotonic()
        last = self._last_request.get(host, 0.0)
        elapsed = now - last
        if elapsed < self._min_delay:
            wait = self._min_delay - elapsed
            time.sleep(wait)
            waited = wait
        else:
            waited = 0.0
        self._last_request[host] = time.monotonic()
        return waited

    def reset(self):
        self._last_request.clear()


class RobotsChecker:
    """Optional robots.txt checker.

    Caches parsed robots.txt per host to avoid repeated fetches.
    Respects crawl-delay when available.
    """

    def __init__(self, user_agent: str | None = None):
        self._user_agent = user_agent or "NeraJob/0.2"
        self._cache: dict[str, robotparser.RobotFileParser | None] = {}
        self._ttl: dict[str, float] = {}
        self._cache_ttl = 3600  # Re-fetch every hour

    def is_allowed(self, url: str, user_agent: str | None = None) -> bool:
        """Check if URL is allowed by robots.txt. Returns True if no robots.txt exists."""
        parsed = urlparse(url)
        host = parsed.netloc or parsed.hostname
        if not host:
            return True

        ua = user_agent or self._user_agent
        robot = self._get_or_fetch(host)
        if robot is None:
            return True  # no robots.txt → allow
        return robot.can_fetch(ua, url)

    def _get_or_fetch(self, host: str) -> RobotFileParser | None:
        now = time.monotonic()
        if host in self._cache and (now - self._ttl.get(host, 0)) < self._cache_ttl:
            return self._cache[host]

        scheme = "https"
        robots_url = f"{scheme}://{host}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        try:
            with httpx.Client(timeout=10, follow_redirects=True) as client:
                resp = client.get(robots_url)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
                self._cache[host] = rp
            else:
                self._cache[host] = None
        except Exception:
            self._cache[host] = None

        self._ttl[host] = time.monotonic()
        return self._cache[host]

    def clear(self):
        self._cache.clear()
        self._ttl.clear()


def _retry_after(response: httpx.Response) -> float | None:
    """Parse Retry-After header or extract from body for common APIs."""
    retry = response.headers.get("Retry-After")
    if retry is not None:
        try:
            return float(retry)
        except ValueError:
            return None
    return None


def create_client(
    user_agent: str | None = None,
    timeout: float | None = None,
    rate_limit_delay: float | None = None,
    max_retries: int = 3,
    backoff_factor: float = 1.0,
) -> httpx.Client:
    """Create an httpx.Client with rate limiting, retries, and robots.txt awareness.

    Args:
        user_agent: Custom User-Agent header. Defaults to NERAJOB_USER_AGENT env or fallback.
        timeout: Request timeout in seconds. Defaults to NERAJOB_HTTP_TIMEOUT env or 20.
        rate_limit_delay: Min seconds between requests to the same host. Default 1.0.
        max_retries: Max retry attempts for 429/5xx responses. Default 3.
        backoff_factor: Base delay multiplier for exponential backoff. Default 1.0.

    Returns:
        An httpx.Client configured with a transport that applies rate limiting and retries.
    """
    from nerajob.config import http_timeout as default_timeout
    from nerajob.config import user_agent as default_ua

    final_ua = user_agent or default_ua()
    final_timeout = timeout if timeout is not None else default_timeout()

    transport = RateLimitedTransport(
        min_delay=rate_limit_delay if rate_limit_delay is not None else 1.0,
        max_retries=max_retries,
        backoff_factor=backoff_factor,
    )

    return httpx.Client(
        timeout=final_timeout,
        headers={"User-Agent": final_ua},
        follow_redirects=True,
        transport=transport,
    )


class RateLimitedTransport(httpx.BaseTransport):
    """HTTPX transport wrapping the default transport with rate limiting and retries."""

    def __init__(
        self,
        min_delay: float = 1.0,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
    ):
        self._transport = httpx.HTTPTransport()
        self._rate_limiter = RateLimiter(min_delay=min_delay).wait_if_needed
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        host = request.url.host or ""
        last_exc = None
        last_response = None

        for attempt in range(self._max_retries + 1):
            # Apply rate limiting before each attempt
            self._rate_limiter(host)

            try:
                response = self._transport.handle_request(request)
            except (httpx.ConnectError, httpx.ReadError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt < self._max_retries:
                    delay = self._backoff_factor * (2**attempt)
                    time.sleep(delay)
                    continue
                raise

            # Retry on 429 (rate limit) and 5xx (server errors)
            if response.status_code in (429, 502, 503, 504):
                if attempt < self._max_retries:
                    retry_after = _retry_after(response)
                    delay = retry_after if retry_after is not None else self._backoff_factor * (2**attempt)
                    time.sleep(delay)
                    last_response = response
                    continue
                # Exhausted retries for error status
                last_response = response
                break

            # Success — return non-retryable response
            return response

        if last_exc:
            raise last_exc
        raise httpx.RequestError("Max retries exceeded", request=request)

    def close(self):
        self._transport.close()