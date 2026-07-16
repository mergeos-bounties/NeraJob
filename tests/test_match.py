from nerajob.match import MatchWeights, match_score, rank_jobs
from nerajob.models import JobPosting, Profile
from nerajob.storage import default_profile


def test_match_score_hits_python() -> None:
    profile = default_profile()
    profile.skills = ["Python", "FastAPI", "SQL"]
    job = JobPosting(
        id="j1",
        source="sample",
        title="Senior Python Backend Engineer",
        company="Acme",
        description="Build FastAPI services with SQL databases",
        tags=["python", "api"],
        remote=True,
    )
    m = match_score(profile, job)
    assert m["score"] >= 40
    assert "python" in m["skill_hits"]


def test_rank_jobs() -> None:
    profile = Profile(skills=["python", "kubernetes"])
    jobs = [
        JobPosting(id="a", source="s", title="K8s Platform", company="X", description="kubernetes", tags=["k8s"]),
        JobPosting(id="b", source="s", title="Sales", company="Y", description="crm", tags=["sales"]),
    ]
    ranked = rank_jobs(profile, jobs, top_k=2)
    assert ranked[0]["job_id"] == "a"


def test_match_score_accepts_custom_weights() -> None:
    profile = Profile(
        headline="Product Manager",
        skills=["python"],
        location="Berlin",
    )
    job = JobPosting(
        id="j2",
        source="sample",
        title="Product Manager",
        company="Acme",
        location="Berlin, Germany",
        description="Own roadmap and customer discovery",
        tags=["product"],
        remote=False,
    )

    score = match_score(
        profile,
        job,
        weights=MatchWeights(skills=0.0, title=80.0, location=20.0),
    )

    assert score["score_weights"] == {"skills": 0.0, "title": 80.0, "location": 20.0}
    assert score["score"] > 60


def test_rank_jobs_uses_custom_weights() -> None:
    profile = Profile(
        headline="Product Manager",
        skills=["python"],
        location="Berlin",
    )
    jobs = [
        JobPosting(
            id="skill",
            source="sample",
            title="Python Backend Engineer",
            company="Acme",
            description="Build Python APIs",
            tags=["python"],
            remote=True,
        ),
        JobPosting(
            id="title-location",
            source="sample",
            title="Product Manager",
            company="Beta",
            location="Berlin",
            description="Own roadmap",
            tags=["product"],
            remote=False,
        ),
    ]

    assert rank_jobs(profile, jobs, top_k=2)[0]["job_id"] == "skill"

    ranked = rank_jobs(
        profile,
        jobs,
        top_k=2,
        weights=MatchWeights(skills=0.0, title=80.0, location=20.0),
    )

    assert ranked[0]["job_id"] == "title-location"
