from __future__ import annotations

import argparse
import re
from pathlib import Path

from nerajob.config import project_root
from nerajob.match import expand_skills
from nerajob.models import JobPosting
from nerajob.scrapers.sample import SampleScraper


def extract_cv_skills(markdown: str) -> list[str]:
    lines = markdown.splitlines()
    in_skills = False
    skill_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.lower() == "## skills":
            in_skills = True
            continue
        if in_skills and stripped.startswith("## "):
            break
        if in_skills and stripped:
            skill_lines.append(stripped)

    raw = " ".join(skill_lines)
    raw = re.sub(r"^[*-]\s*", "", raw)
    parts = re.split(r"[,;|/]|(?:\s+-\s+)", raw)
    skills = [part.strip(" -*`").lower() for part in parts]
    return sorted({skill for skill in skills if skill})


def skills_gap_report(cv_markdown: str, job: JobPosting) -> dict:
    cv_skills = extract_cv_skills(cv_markdown)
    expanded_cv = expand_skills(cv_skills)
    job_tags = [tag.strip().lower() for tag in job.tags if tag.strip()]

    matched = []
    missing = []
    for tag in job_tags:
        aliases = expand_skills({tag})
        if expanded_cv & aliases:
            matched.append(tag)
        else:
            missing.append(tag)

    coverage = (len(matched) / len(job_tags) * 100.0) if job_tags else 100.0
    return {
        "job_id": job.id,
        "job_title": job.title,
        "company": job.company,
        "cv_skills": cv_skills,
        "job_tags": job_tags,
        "matched_skills": matched,
        "missing_skills": missing,
        "coverage": round(coverage, 1),
        "recommendations": _recommendations(missing),
    }


def render_skills_gap_markdown(report: dict) -> str:
    lines = [
        "# Skills Gap Report",
        "",
        f"Job: **{report['job_title']}** at **{report['company']}**",
        f"Coverage: **{report['coverage']}%** of job tags found in the CV skill set.",
        "",
        "## Matched skills",
        _bullet_list(report["matched_skills"], empty="No direct skill matches found."),
        "",
        "## Missing skills",
        _bullet_list(report["missing_skills"], empty="No missing job tags detected."),
        "",
        "## Recommendations",
        _bullet_list(report["recommendations"], empty="No recommendations."),
        "",
        "## CV skills parsed",
        ", ".join(report["cv_skills"]) or "No skills parsed.",
        "",
    ]
    return "\n".join(lines)


def write_demo_report(
    cv_path: Path | None = None,
    out_path: Path | None = None,
    query: str = "platform",
) -> Path:
    root = project_root()
    cv = cv_path or (root / "data" / "cv" / "cv-python-backend.md")
    out = out_path or (root / "data" / "reports" / "skills_gap_report.md")
    jobs = SampleScraper().search(query=query, limit=1)
    if not jobs:
        jobs = SampleScraper().search(query="", limit=1)
    report = skills_gap_report(cv.read_text(encoding="utf-8"), jobs[0])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_skills_gap_markdown(report), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    root = project_root()
    parser = argparse.ArgumentParser(description="Generate an offline CV vs job skills gap report.")
    parser.add_argument("--cv", type=Path, default=root / "data" / "cv" / "cv-python-backend.md")
    parser.add_argument("--query", default="platform", help="Offline sample job query")
    parser.add_argument("--out", type=Path, default=root / "data" / "reports" / "skills_gap_report.md")
    args = parser.parse_args(argv)
    print(write_demo_report(cv_path=args.cv, out_path=args.out, query=args.query))
    return 0


def _recommendations(missing: list[str]) -> list[str]:
    if not missing:
        return ["Keep the CV aligned with the target role and add measurable impact examples."]
    return [
        f"Add a short project bullet or training note for `{skill}` if you have real evidence."
        for skill in missing
    ]


def _bullet_list(items: list[str], empty: str) -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in items)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
