from __future__ import annotations

from pathlib import Path

from nerajob.models import JobPosting
from nerajob.skills_gap import extract_cv_skills, skills_gap_report, write_demo_report


def test_extract_cv_skills_from_markdown() -> None:
    cv = Path("data/cv/cv-python-backend.md").read_text(encoding="utf-8")
    skills = extract_cv_skills(cv)
    assert {"python", "apis", "sql"}.issubset(set(skills))


def test_skills_gap_report_identifies_missing_job_tags() -> None:
    cv = "# Candidate\n\n## Skills\nPython, APIs, SQL\n"
    job = JobPosting(
        id="j1",
        source="sample",
        title="Platform Engineer",
        company="Orbit Systems",
        tags=["python", "kubernetes", "aws"],
    )
    report = skills_gap_report(cv, job)
    assert report["coverage"] == 33.3
    assert report["matched_skills"] == ["python"]
    assert report["missing_skills"] == ["kubernetes", "aws"]


def test_write_demo_report_offline(tmp_path) -> None:
    out = write_demo_report(out_path=tmp_path / "skills_gap.md")
    text = out.read_text(encoding="utf-8")
    assert "Skills Gap Report" in text
    assert "Missing skills" in text
