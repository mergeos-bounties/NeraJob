from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx

from nerajob.config import http_timeout, user_agent

REJECTED_STATUSES = {429, 500, 502, 503, 504}


@dataclass
class _RateState:
    last: float = 0.0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class ScraperHTTPClient:
    """
    Shared async HTTP client with configurable timeout/user-agent,
    per-host rate limiting, exponential-backoff retry for 429/5xx,
    and optional robots.txt compliance checking.
    """

    def __init__(
        self,
        timeout: float | None = None,
        ua: str | None = None,
        max_retries: int = 3,
        requests_per_second: float = 5.0,
        respect_robots: bool = True,
    ) -> None:
        self.timeout = http_timeout() if timeout is None else timeout
        self.user_agent = user_agent() if ua is None else ua
        self.max_retries = max_retries
        self.requests_per_second = requests_per_second
        self.respect_robots = respect_robots

        self._client: httpx.AsyncClient | None = None
        self._rate: dict[str, _RateState] = defaultdict(_RateState)
        self._robots_cache: dict[str, list[tuple[str, str]]] = {}
        self._robots_lock = asyncio.Lock()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
            )
        return self._client

    async def get(self, url: str, **kwargs: object) -> httpx.Response:
        parsed = urlparse(url)
        host = parsed.netloc or parsed.path

        if self.respect_robots:
            allowed = await self._robots_allowed(url)
            if not allowed:
                raise httpx.HTTPStatusError(
                    f"Blocked by robots.txt: {url}",
                    request=httpx.Request("GET", url),
                    response=httpx.Response(403),
                )

        await self._throttle(host)
        return await self._request_with_retry(url, **kwargs)

    async def _throttle(self, host: str) -> None:
        state = self._rate[host]
        min_interval = 1.0 / max(self.requests_per_second, 0.1)
        async with state.lock:
            elapsed = time.monotonic() - state.last
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            state.last = time.monotonic()

    async def _request_with_retry(self, url: str, **kwargs: object) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                client = await self._get_client()
                resp = await client.get(url, **kwargs)
                if resp.status_code in REJECTED_STATUSES and attempt < self.max_retries:
                    wait = 2 ** attempt + (attempt * 0.5)
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    wait = 2 ** attempt + (attempt * 0.5)
                    await asyncio.sleep(wait)
        raise last_exc if last_exc is not None else RuntimeError("unreachable")

    async def _robots_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = f"{base}/robots.txt"

        async with self._robots_lock:
            if base not in self._robots_cache:
                self._robots_cache[base] = await self._fetch_robots_rules(robots_url)
            rules = self._robots_cache[base]

        path = parsed.path or "/"
        return _is_path_allowed(path, self.user_agent, rules)

    async def _fetch_robots_rules(self, robots_url: str) -> list[tuple[str, str]]:
        try:
            client = await self._get_client()
            resp = await client.get(robots_url, timeout=10)
            if resp.status_code == 200:
                return _parse_robots(resp.text)
        except Exception:
            pass
        return []

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


def _parse_robots(text: str) -> list[tuple[str, str]]:
    """Parse a robots.txt body into (directive, path) pairs."""
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            lines.append((key.strip().lower(), val.strip()))
    return lines


def _is_path_allowed(
    path: str, ua: str, rules: list[tuple[str, str]]
) -> bool:
    """Check if *path* is allowed for *ua* per a parsed set of robots rules."""
    applicable: list[tuple[str, str]] = []
    in_group = False
    for directive, value in rules:
        if directive == "user-agent":
            in_group = value == "*" or value.lower() in ua.lower()
        elif in_group and directive in ("allow", "disallow"):
            applicable.append((directive, value))

    allowed = True
    for directive, value in applicable:
        pattern = value if value else "/"
        if not path.startswith(pattern):
            continue
        if directive == "disallow":
            allowed = False
        elif directive == "allow":
            allowed = True
    return allowed
