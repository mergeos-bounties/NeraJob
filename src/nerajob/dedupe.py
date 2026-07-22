"""Deduplication helpers for multi-source job scanning."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _dedupe_key(job: dict) -> tuple:
    url = (job.get("url") or "").strip().lower()
    if url:
        return ("url", url)
    title = (job.get("title") or "").strip().lower()
    company = (job.get("company") or "").strip().lower()
    return ("title_company", title, company)


def dedupe(jobs: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    result: list[dict] = []
    for job in jobs:
        key = _dedupe_key(job)
        if key in seen:
            logger.debug("Skipping duplicate: %s", key)
            continue
        seen.add(key)
        result.append(job)
    return result


def dedupe_report(jobs: list[dict]) -> dict:
    seen_urls: set[str] = set()
    seen_tc: set[tuple] = set()
    unique: list[dict] = []
    dupes = 0
    for job in jobs:
        url = (job.get("url") or "").strip().lower()
        if url:
            if url in seen_urls:
                dupes += 1
                continue
            seen_urls.add(url)
        else:
            title = (job.get("title") or "").strip().lower()
            company = (job.get("company") or "").strip().lower()
            key = (title, company)
            if key in seen_tc:
                dupes += 1
                continue
            seen_tc.add(key)
        unique.append(job)
    return {
        "total": len(jobs),
        "unique": len(unique),
        "duplicates_removed": dupes,
    }
