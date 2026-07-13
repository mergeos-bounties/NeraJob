from nerajob.match import match_score
from nerajob.models import JobPosting, Profile


def test_remote_job_gets_location_boost():
    profile = Profile(
        full_name="A",
        headline="Engineer",
        location="Remote",
        skills=["python"],
    )
    job = JobPosting(
        id="j1",
        source="test",
        title="Python Engineer",
        company="Acme",
        location="Worldwide",
        description="Build APIs with Python",
        tags=["python"],
        remote=True,
        url="https://example.com/j1",
    )
    r = match_score(profile, job)
    assert r["location_boost"] >= 10.0
    assert r["score"] > 0
