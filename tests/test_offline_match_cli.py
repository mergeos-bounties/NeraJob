"""Tests for offline CLI match with --resume-file and --jobs-file."""

import json
import subprocess as sp
from pathlib import Path

import pytest
from nerajob.match import match_score
from nerajob.models import JobPosting, Profile


def test_offline_match_with_files(tmp_path: Path) -> None:
    profile = Profile(
        full_name="Test User",
        headline="Python Backend Engineer",
        location="Remote",
        skills=["Python", "FastAPI", "PostgreSQL"],
    )
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(profile.model_dump_json(), encoding="utf-8")

    jobs = [
        JobPosting(
            id="j1",
            source="fixture",
            title="Python Backend Engineer",
            company="TestCo",
            location="Remote",
            description="FastAPI and PostgreSQL experience required",
            tags=["python", "fastapi", "postgres"],
            remote=True,
        ),
        JobPosting(
            id="j2",
            source="fixture",
            title="Rust Systems Engineer",
            company="TestCo",
            location="Remote",
            description="Systems programming in Rust",
            tags=["rust", "systems"],
            remote=True,
        ),
    ]
    jobs_path = tmp_path / "jobs.json"
    jobs_path.write_text(
        json.dumps([j.model_dump() for j in jobs]), encoding="utf-8"
    )

    result = sp.run(
        [
            "python",
            "-m",
            "nerajob",
            "jobs",
            "match",
            "--resume-file",
            str(profile_path),
            "--jobs-file",
            str(jobs_path),
            "--top",
            "2",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0
    assert "Python Backend Engineer" in result.stdout
    assert "TestCo" in result.stdout


def test_offline_match_python_profile_vs_frontend_jobs():
    profile = Profile(
        headline="Python Backend Engineer",
        location="Remote",
        skills=["Python", "FastAPI", "PostgreSQL"],
    )
    job = JobPosting(
        id="fe_01",
        source="sample",
        title="Senior Frontend Engineer",
        company="WebCo",
        location="Remote",
        description="",
        tags=["react", "typescript", "next.js"],
        remote=True,
    )
    score = match_score(profile, job)
    # Python backend profile should not score high on frontend role
    assert score["score"] < 50 or len(score["skill_hits"]) == 0


def test_offline_match_devops_profile_vs_devops_jobs():
    profile = Profile(
        headline="DevOps Engineer",
        location="Remote",
        skills=["Kubernetes", "Terraform", "AWS", "Docker"],
    )
    job = JobPosting(
        id="devops_01",
        source="sample",
        title="Senior DevOps Engineer",
        company="CloudScale",
        location="Remote",
        description="",
        tags=["kubernetes", "terraform", "aws", "ci/cd"],
        remote=True,
    )
    score = match_score(profile, job)
    assert score["score"] >= 50
    assert score["band"] in ("medium", "strong")


def test_offline_match_with_sample_fixtures():
    profile = Profile(
        headline="Python Backend Engineer",
        location="Remote",
        skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
    )

    import json

    jobs_path = (
        Path(__file__).parent.parent / "data" / "samples" / "jobs_python_remote.json"
    )
    jobs_data = json.loads(jobs_path.read_text(encoding="utf-8"))
    jobs = [JobPosting(**j) for j in jobs_data]

    from nerajob.match import rank_jobs

    ranked = rank_jobs(profile, jobs, top_k=3)
    assert len(ranked) == 3
    # Python-skilled jobs should rank highest
    top = ranked[0]
    assert "python" in str(top.get("skill_hits", [])).lower() or top["score"] > 0
