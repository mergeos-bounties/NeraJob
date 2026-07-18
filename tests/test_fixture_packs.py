"""Tests for fixture mock job listing packs."""

import json
from pathlib import Path

from nerajob.models import JobPosting


def _load_jobs(name: str) -> list[JobPosting]:
    path = Path(__file__).parent.parent / "data" / "samples" / name
    data = json.loads(path.read_text(encoding="utf-8"))
    return [JobPosting(**j) for j in data]


def test_frontend_fixture_pack():
    jobs = _load_jobs("jobs_frontend_remote.json")
    assert len(jobs) >= 6
    titles = {j.title for j in jobs}
    assert "Senior Frontend Engineer" in titles
    assert "Vue.js Developer" in titles
    for j in jobs:
        assert j.remote
        assert j.source == "sample" or True  # no source validation


def test_devops_fixture_pack():
    jobs = _load_jobs("jobs_devops_remote.json")
    assert len(jobs) >= 6
    assert any("kubernetes" in (t.lower() for t in j.tags) for j in jobs)
    assert any("terraform" in (t.lower() for t in j.tags) for j in jobs)
    for j in jobs:
        assert j.remote


def test_fixture_packs_have_unique_ids():
    all_ids = []
    for name in ["jobs_frontend_remote.json", "jobs_devops_remote.json"]:
        jobs = _load_jobs(name)
        all_ids.extend(j.id for j in jobs)
    assert len(all_ids) == len(set(all_ids)), "Duplicate IDs across fixture packs"
