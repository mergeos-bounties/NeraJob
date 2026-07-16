import json
from pathlib import Path

from nerajob.evaluation import precision_at_k
from nerajob.match import rank_jobs
from nerajob.models import JobPosting, Profile


ROOT = Path(__file__).parent.parent


def _load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_offline_resume_fixtures_have_perfect_precision_at_one() -> None:
    jobs = [JobPosting(**item) for item in _load_json(ROOT / "data" / "samples" / "jobs_match_precision.json")]
    cases = _load_json(Path(__file__).parent / "fixtures" / "resume_match_cases.json")

    for case in cases:
        profile = Profile(**case["profile"])
        ranked_ids = [item["job_id"] for item in rank_jobs(profile, jobs, top_k=3)]
        assert precision_at_k(ranked_ids, case["relevant_job_ids"], 1) == 1.0, case["name"]


def test_precision_at_k_handles_short_rankings_and_rejects_invalid_k() -> None:
    assert precision_at_k(["match"], ["match"], 3) == 1.0
    assert precision_at_k([], ["match"], 1) == 0.0

    try:
        precision_at_k(["match"], ["match"], 0)
    except ValueError as error:
        assert str(error) == "k must be at least 1"
    else:
        raise AssertionError("expected invalid k to raise ValueError")
