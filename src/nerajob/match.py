"""Score how well a job posting matches a local profile."""

from __future__ import annotations

from nerajob.models import JobPosting, Profile

# Common skill aliases for resume ↔ job matching (offline-friendly).
SKILL_ALIASES: dict[str, set[str]] = {
    "python": {"python", "django", "fastapi", "flask"},
    "javascript": {"javascript", "js", "typescript", "node", "react"},
    "devops": {"devops", "docker", "kubernetes", "k8s", "ci/cd"},
    "ml": {"ml", "machine learning", "pytorch", "tensorflow"},
    "rust": {"rust", "cargo", "tokio", "actix", "axum"},
    "go": {"go", "golang", "gin", "fiber"},
    "sql": {"sql", "postgres", "postgresql", "mysql", "sqlite", "database"},
    "cloud": {"cloud", "aws", "gcp", "azure", "s3", "lambda"},
    "java": {"java", "spring", "kotlin", "jvm", "maven", "gradle"},
}


def expand_skills(skills: set[str] | list[str] | tuple[str, ...]) -> set[str]:
    out = {str(s).lower().strip() for s in skills if str(s).strip()}
    for s in list(out):
        for key, aliases in SKILL_ALIASES.items():
            if s == key or s in aliases:
                out |= aliases | {key}
    return out


def match_score(profile: Profile, job: JobPosting) -> dict:
    """
    Lightweight keyword match: skills vs title/description/tags + location soft score.
    Returns 0–100 score with explainable hits.
    """
    base_skills = [s.strip().lower() for s in (profile.skills or []) if s.strip()]
    hay = f"{job.title} {job.description} {' '.join(job.tags)} {job.company}".lower()
    hits: list[str] = []
    for s in base_skills:
        aliases = expand_skills({s})
        if any(a and a in hay for a in aliases):
            hits.append(s)
    skill_score = (len(hits) / max(1, len(base_skills))) * 70.0 if base_skills else 35.0

    # headline / target role token overlap with job title
    headline_tokens = {
        t for t in (profile.headline or "").lower().replace("/", " ").split() if len(t) > 2
    }
    title_tokens = {t for t in job.title.lower().replace("/", " ").split() if len(t) > 2}
    role_overlap = headline_tokens & title_tokens
    role_score = min(20.0, len(role_overlap) * 7.0)

    loc_score = 0.0
    pl = (profile.location or "").lower()
    jl = (job.location or "").lower()
    prefers_remote = any(
        tok in pl for tok in ("remote", "wfh", "anywhere", "worldwide")
    ) or getattr(profile, "remote_ok", False)
    if job.remote or "remote" in jl:
        loc_score = 12.0 if prefers_remote else 10.0
    elif pl and any(part in jl for part in pl.split() if len(part) > 2):
        loc_score = 10.0

    total = min(100.0, skill_score + role_score + loc_score)
    return {
        "job_id": job.id,
        "title": job.title,
        "company": job.company,
        "score": round(total, 1),
        "skill_hits": hits,
        "role_overlap": sorted(role_overlap),
        "remote": job.remote,
        "location_boost": loc_score,
        "band": "strong" if total >= 70 else "medium" if total >= 40 else "weak",
    }


def rank_jobs(profile: Profile, jobs: list[JobPosting], top_k: int = 20) -> list[dict]:
    ranked = [match_score(profile, j) for j in jobs]
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked[: max(1, top_k)]
