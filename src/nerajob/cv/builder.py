from __future__ import annotations

from pathlib import Path

from slugify import slugify

from nerajob.config import data_dir
from nerajob.models import Profile


def build_cv_markdown(profile: Profile, target_role: str = "") -> str:
    role = target_role.strip() or profile.headline
    skills = ", ".join(profile.skills)
    lines = [
        f"# {profile.full_name}",
        f"**{role}**  ",
        f"{profile.location} · {profile.email}"
        + (f" · {profile.phone}" if profile.phone else ""),
        "",
    ]
    if profile.links:
        lines.append(" · ".join(profile.links))
        lines.append("")
    lines.extend(
        [
            "## Summary",
            profile.summary,
            "",
            "## Skills",
            skills or "—",
            "",
            "## Experience",
        ]
    )
    for exp in profile.experience:
        lines.append(f"### {exp.title} — {exp.company}")
        lines.append(f"*{exp.start} – {exp.end}*")
        for h in exp.highlights:
            lines.append(f"- {h}")
        lines.append("")
    if profile.education:
        lines.append("## Education")
        for edu in profile.education:
            bit = " · ".join(
                [x for x in [edu.degree, edu.school, edu.year] if x]
            )
            lines.append(f"- {bit}")
        lines.append("")
    if profile.languages:
        lines.append("## Languages")
        lines.append(", ".join(profile.languages))
        lines.append("")
    if target_role:
        lines.extend(
            [
                "## Target role notes",
                f"Tailored for **{target_role}**. Emphasize overlapping skills and impact metrics before sending.",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def write_cv_files(
    profile: Profile, target_role: str = "", formats: list[str] | None = None
) -> dict[str, Path | None]:
    """
    Generate CV files in the requested formats.
    Returns a dict mapping format to Path (or None if generation failed).
    """
    if formats is None:
        formats = ["markdown", "text"]

    # Prepare common data
    md = build_cv_markdown(profile, target_role)
    slug = slugify(target_role or profile.headline or "general") or "general"
    out_dir = data_dir() / "cv"
    out_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Path | None] = {fmt: None for fmt in formats}

    # Markdown
    if "markdown" in formats:
        md_path = out_dir / f"cv-{slug}.md"
        md_path.write_text(md, encoding="utf-8")
        result["markdown"] = md_path

    # Plain text (strip markdown markers)
    if "text" in formats:
        txt_path = out_dir / f"cv-{slug}.txt"
        plain = (
            md.replace("# ", "")
            .replace("## ", "")
            .replace("### ", "")
            .replace("**", "")
            .replace("*", "")
        )
        txt_path.write_text(plain, encoding="utf-8")
        result["text"] = txt_path

    # PDF (optional)
    if "pdf" in formats:
        try:
            import markdown
            from weasyprint import HTML
        except ImportError:
            # Dependencies not installed; skip PDF
            pass
        else:
            # Convert markdown to HTML
            html = markdown.markdown(md)
            pdf_path = out_dir / f"cv-{slug}.pdf"
            HTML(string=html).write_pdf(pdf_path)
            result["pdf"] = pdf_path

    return result
