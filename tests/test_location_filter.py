"""Tests for location filter using remote-only job fixture."""
from __future__ import annotations

import json
from pathlib import Path

from nerajob.models import JobPosting


FIXTURE_PATH = Path(__file__).resolve().parent.parent / "data" / "samples" / "jobs_remote_only.json"


def load_fixture() -> list[JobPosting]:
    """Load the remote-only job fixture and validate."""
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return [JobPosting.model_validate(item) for item in raw]


def test_fixture_file_exists() -> None:
    """Fixture JSON file must exist."""
    assert FIXTURE_PATH.exists(), f"Missing fixture: {FIXTURE_PATH}"


def test_fixture_parses_to_job_postings() -> None:
    """All entries must parse into valid JobPosting objects."""
    jobs = load_fixture()
    assert len(jobs) == 5
    for job in jobs:
        assert isinstance(job, JobPosting)
        assert job.source == "fixture"


def test_all_jobs_are_remote() -> None:
    """Every job in the remote-only fixture must have remote=True."""
    jobs = load_fixture()
    for job in jobs:
        assert job.remote is True, f"Job {job.id} is not remote: {job.remote}"


def test_location_filter_keeps_only_remote() -> None:
    """Location filter should keep all jobs when filtering for remote=True."""
    jobs = load_fixture()
    # Simulate a location filter: keep jobs where remote==True
    remote_only = [j for j in jobs if j.remote]
    assert len(remote_only) == len(jobs)
    assert len(remote_only) == 5


def test_location_filter_drops_non_remote() -> None:
    """When mixing remote and on-site, location filter drops non-remote jobs."""
    jobs = load_fixture()
    # Add one on-site job to the mix
    onsite = JobPosting(
        id="onsite_001",
        source="fixture",
        title="Office Manager",
        company="LocalCorp",
        location="New York, NY",
        url="https://example.com/jobs/onsite_001",
        description="On-site office management.",
        tags=["admin"],
        salary="$50k-$70k",
        remote=False,
    )
    all_jobs = jobs + [onsite]
    # Filter for remote only
    remote_only = [j for j in all_jobs if j.remote]
    assert len(remote_only) == 5
    assert onsite not in remote_only
    # Verify remote jobs have recognizable remote locations
    remote_locations = {j.location.lower() for j in remote_only}
    assert any("remote" in loc for loc in remote_locations)


def test_remote_jobs_have_expected_fields() -> None:
    """Each remote job in the fixture must have required fields populated."""
    jobs = load_fixture()
    for job in jobs:
        assert job.id, f"Job missing id"
        assert job.title, f"Job {job.id} missing title"
        assert job.company, f"Job {job.id} missing company"
        assert job.tags, f"Job {job.id} missing tags"
        assert job.remote is True, f"Job {job.id} remote is not True"
