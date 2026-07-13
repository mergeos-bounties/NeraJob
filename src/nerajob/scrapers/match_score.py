"""
Match score: rank jobs against a profile's skills.

Computes a relevance score (0–100) for each JobPosting based on
overlap between job tags and profile skills.
"""
from __future__ import annotations

from nerajob.models import JobPosting, Profile


def compute_match_score(job: JobPosting, profile: Profile) -> float:
    """
    Compute a relevance score (0.0–100.0) for a job given a profile.

    Strategy:
      - Tokenise tags and skills (lowercased, stripped)
      - Exact overlap: count matched skills / total profile skills
      - Bonus: partial word match (skill substring in tag or vice versa)
      - Normalise to 0–100
    """
    if not profile.skills:
        return 0.0

    profile_skills = {s.lower().strip() for s in profile.skills if s.strip()}
    job_tags = {t.lower().strip() for t in job.tags if t.strip()}

    if not profile_skills or not job_tags:
        return 0.0

    # Exact matches
    exact = profile_skills & job_tags

    # Partial matches (substring in either direction)
    partial = set()
    for skill in profile_skills:
        for tag in job_tags:
            if skill != tag and (skill in tag or tag in skill):
                partial.add(skill)
                break

    matched = exact | partial
    return round(len(matched) / len(profile_skills) * 100, 1)


def rank_jobs(jobs: list[JobPosting], profile: Profile) -> list[tuple[JobPosting, float]]:
    """
    Rank jobs by match score (descending).

    Returns list of (job, score) tuples sorted by score highest first.
    """
    scored = [(job, compute_match_score(job, profile)) for job in jobs]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored