"""Tests for the match score module."""
from datetime import datetime, timezone

from nerajob.models import JobPosting, Profile
from nerajob.scrapers.match_score import compute_match_score, rank_jobs


def _job(id: str, title: str, company: str, tags: list[str]) -> JobPosting:
    return JobPosting(
        id=id,
        source="test",
        title=title,
        company=company,
        location="Remote",
        url="https://example.com",
        description="desc",
        tags=tags,
        remote=True,
        scraped_at=datetime.now(timezone.utc).isoformat(),
    )


def _profile(skills: list[str]) -> Profile:
    return Profile(
        full_name="Test User",
        email="test@example.com",
        skills=skills,
    )


def test_exact_skill_match():
    profile = _profile(["python", "fastapi", "sql"])
    job = _job("1", "Senior Python Engineer", "PyTech", ["python", "fastapi", "aws"])
    score = compute_match_score(job, profile)
    assert score == 66.7  # 2/3 matched


def test_no_match():
    profile = _profile(["java", "spring"])
    job = _job("1", "Python Developer", "PyTech", ["python", "fastapi"])
    score = compute_match_score(job, profile)
    assert score == 0.0


def test_partial_match():
    profile = _profile(["python", "api"])
    job = _job("1", "Python Engineer", "PyTech", ["Python3", "fastapi"])
    score = compute_match_score(job, profile)
    # python -> Python3 partial match; api -> fastapi partial match => 2/2 = 100%
    assert score == 100.0


def test_empty_profile():
    profile = _profile([])
    job = _job("1", "Python Engineer", "PyTech", ["python"])
    score = compute_match_score(job, profile)
    assert score == 0.0


def test_empty_job_tags():
    profile = _profile(["python"])
    job = _job("1", "Python Engineer", "PyTech", [])
    score = compute_match_score(job, profile)
    assert score == 0.0


def test_rank_jobs_sorted():
    profile = _profile(["python", "fastapi"])
    jobs = [
        _job("1", "Python Dev", "A", ["java"]),        # 0%
        _job("2", "Python Engineer", "B", ["python", "aws"]),  # 50%
        _job("3", "FastAPI Dev", "C", ["fastapi"]),    # 50%
        _job("4", "Python FastAPI Lead", "D", ["python", "fastapi", "sql"]),  # 100%
    ]
    ranked = rank_jobs(jobs, profile)
    scores = [s for _, s in ranked]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] == 100.0


def test_rank_jobs_preserves_top_scorer():
    profile = _profile(["python"])
    jobs = [
        _job("1", "Python Dev", "A", ["python"]),
        _job("2", "Java Dev", "B", ["java"]),
    ]
    ranked = rank_jobs(jobs, profile)
    assert ranked[0][0].id == "1"
    assert ranked[0][1] == 100.0


def test_case_insensitive_match():
    profile = _profile(["Python", "FastAPI"])
    job = _job("1", "Senior python engineer", "PyTech", ["PYTHON", "fastapi"])
    score = compute_match_score(job, profile)
    assert score == 100.0