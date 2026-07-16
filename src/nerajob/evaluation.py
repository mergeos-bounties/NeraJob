"""Offline evaluation helpers for deterministic job-match fixtures."""

from __future__ import annotations

from collections.abc import Iterable


def precision_at_k(ranked_job_ids: Iterable[str], relevant_job_ids: Iterable[str], k: int) -> float:
    """Return the fraction of the first *k* ranked jobs that are relevant."""
    if k < 1:
        raise ValueError("k must be at least 1")

    ranked = list(ranked_job_ids)[:k]
    if not ranked:
        return 0.0

    relevant = set(relevant_job_ids)
    return sum(job_id in relevant for job_id in ranked) / len(ranked)
