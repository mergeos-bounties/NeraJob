"""Tests for `nerajob jobs list --sort match`."""

from pathlib import Path

from nerajob.match import MatchWeights, match_score
from nerajob.models import JobPosting, Profile
from nerajob.storage import default_profile


def test_match_sort_orders_by_score_descending() -> None:
    profile = default_profile()
    profile.skills = ["Python", "FastAPI", "SQL"]
    jobs = [
        JobPosting(
            id="high",
            source="sample",
            title="Senior Python Backend Engineer",
            company="Acme",
            description="Build FastAPI services with SQL databases",
            tags=["python", "api"],
            remote=True,
        ),
        JobPosting(
            id="low",
            source="sample",
            title="Rust Systems Engineer",
            company="Other",
            description="Low-level systems programming",
            tags=["rust", "systems"],
            remote=True,
        ),
        JobPosting(
            id="mid",
            source="sample",
            title="Data Analyst Python",
            company="DataCo",
            description="Analyze data with SQL",
            tags=["python", "sql"],
            remote=True,
        ),
    ]

    scored = [(job, match_score(profile, job)) for job in jobs]
    scored.sort(key=lambda x: x[1]["score"], reverse=True)

    assert scored[0][0].id == "high"
    assert scored[0][1]["score"] >= scored[1][1]["score"]
    assert scored[1][1]["score"] >= scored[2][1]["score"]


def test_match_sort_includes_score_in_result() -> None:
    profile = default_profile()
    profile.skills = ["Python"]
    job = JobPosting(
        id="j1",
        source="sample",
        title="Python Developer",
        company="Acme",
        description="Python development",
        tags=["python"],
        remote=True,
    )
    m = match_score(profile, job)
    assert "score" in m
    assert isinstance(m["score"], (int, float))


def test_match_sort_respects_custom_weights() -> None:
    profile = Profile(
        headline="Sales Engineer",
        skills=["python"],
        location="Berlin",
    )
    jobs = [
        JobPosting(
            id="sales",
            source="sample",
            title="Sales Engineer",
            company="TechCo",
            location="Berlin",
            description="Own technical sales",
            tags=["sales"],
            remote=False,
        ),
        JobPosting(
            id="python",
            source="sample",
            title="Python Developer",
            company="CodeCo",
            description="Python development",
            tags=["python"],
            remote=True,
        ),
    ]

    scored_skill = [(job, match_score(profile, job)) for job in jobs]
    scored_skill.sort(key=lambda x: x[1]["score"], reverse=True)
    assert scored_skill[0][0].id == "python"

    weights = MatchWeights(skills=0.0, title=80.0, location=20.0)
    scored_title = [(job, match_score(profile, job, weights=weights)) for job in jobs]
    scored_title.sort(key=lambda x: x[1]["score"], reverse=True)
    assert scored_title[0][0].id == "sales"


def test_match_sort_handles_empty_profile_skills() -> None:
    profile = Profile(skills=[])
    job = JobPosting(
        id="j1",
        source="sample",
        title="Engineer",
        company="Acme",
        tags=[],
    )
    m = match_score(profile, job)
    assert m["score"] >= 0
    assert m["skill_hits"] == []
