from __future__ import annotations

from pathlib import Path

from nerajob.config import APPLICATIONS_DIR
from nerajob.cv.builder import write_cv_files
from nerajob.models import ApplicationPackage, JobPosting, Profile
from nerajob.storage import save_application


def build_cover_note(profile: Profile, job: JobPosting) -> str:
    skill_overlap = [s for s in profile.skills if s.lower() in (job.description + " " + " ".join(job.tags)).lower()]
    skill_line = ", ".join(skill_overlap[:6]) or ", ".join(profile.skills[:4])
    return (
        f"Dear {job.company} hiring team,\n\n"
        f"I am applying for the {job.title} role. I am a {profile.headline} based in {profile.location}. "
        f"My background includes: {skill_line}.\n\n"
        f"{profile.summary}\n\n"
        f"I would welcome the chance to discuss how I can help {job.company}.\n\n"
        f"Best regards,\n{profile.full_name}\n{profile.email}\n"
    )


def build_checklist(job: JobPosting) -> list[str]:
    return [
        f"Read the full posting: {job.url or '(no url)'}",
        "Tailor top 3 CV bullets to the job keywords",
        "Export PDF from Markdown if required by the employer",
        "Customize cover note with one company-specific sentence",
        "Double-check email, phone, and portfolio links",
        "Submit application and log date + channel",
        "Set a follow-up reminder (5–7 business days)",
    ]


def prepare_application(profile: Profile, job: JobPosting) -> tuple[ApplicationPackage, Path]:
    cv_paths = write_cv_files(profile, target_role=job.title)
    package = ApplicationPackage(
        job_id=job.id,
        cover_note=build_cover_note(profile, job),
        checklist=build_checklist(job),
        cv_markdown_path=str(cv_paths["markdown"]),
        notes=f"Source={job.source}; company={job.company}",
    )
    json_path = save_application(package)

    # Also write human-readable package folder
    pack_dir = APPLICATIONS_DIR / job.id
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "cover_note.txt").write_text(package.cover_note, encoding="utf-8")
    (pack_dir / "checklist.md").write_text(
        "# Apply checklist\n\n" + "\n".join(f"- [ ] {item}" for item in package.checklist) + "\n",
        encoding="utf-8",
    )
    (pack_dir / "job.txt").write_text(
        f"{job.title}\n{job.company}\n{job.location}\n{job.url}\n\n{job.description}\n",
        encoding="utf-8",
    )
    # copy cv markdown into package
    target_cv = pack_dir / "cv.md"
    target_cv.write_text(Path(package.cv_markdown_path).read_text(encoding="utf-8"), encoding="utf-8")
    return package, json_path
