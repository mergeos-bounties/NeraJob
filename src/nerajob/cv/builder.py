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
            bit = " · ".join(x for x in [edu.degree, edu.school, edu.year] if x)
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


def _md_to_simple_html(md: str) -> str:
    parts = ["<!DOCTYPE html><html><head><meta charset='utf-8'><style>"]
    parts.append(
        "body{font-family:Helvetica,Arial,sans-serif;line-height:1.5;max-width:800px;"
        "margin:40px auto;padding:0 20px;color:#222}"
        "h1{font-size:24px}h2{font-size:18px;border-bottom:1px solid #ccc;padding-bottom:4px}"
        "h3{font-size:16px}ul{padding-left:20px}li{margin:2px 0}"
    )
    parts.append("</style></head><body>")
    in_list = False
    for line in md.split("\n"):
        if line.startswith("### "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("# "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("- "):
            if not in_list:
                parts.append("<ul>")
                in_list = True
            parts.append(f"<li>{line[2:]}</li>")
        elif line.startswith("*") and line.endswith("*"):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<p><em>{line.strip('*')}</em></p>")
        elif line.strip() == "":
            if in_list:
                parts.append("</ul>")
                in_list = False
        else:
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<p>{line}</p>")
    if in_list:
        parts.append("</ul>")
    parts.append("</body></html>")
    return "\n".join(parts)


def write_cv_pdf(profile: Profile, target_role: str = "") -> Path | None:
    md = build_cv_markdown(profile, target_role)
    slug = slugify(target_role or profile.headline or "general") or "general"
    out_dir = data_dir() / "cv"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"cv-{slug}.pdf"
    html = _md_to_simple_html(md)
    try:
        from weasyprint import HTML as WeasyprintHTML

        WeasyprintHTML(string=html).write_pdf(pdf_path)
    except ImportError:
        try:
            from fpdf import FPDF

            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            for line in md.split("\n"):
                if line.startswith("# "):
                    pdf.set_font("Helvetica", "B", 16)
                    pdf.cell(0, 10, line[2:], new_x="LMARGIN", new_y="NEXT")
                elif line.startswith("## ") or line.startswith("### "):
                    pdf.set_font("Helvetica", "B", 14)
                    label = line[line.index(" ") + 1 :]
                    pdf.cell(0, 10, label, new_x="LMARGIN", new_y="NEXT")
                elif line.strip():
                    pdf.set_font("Helvetica", "", 11)
                    safe = line.encode("latin-1", "replace").decode("latin-1")
                    pdf.multi_cell(0, 6, safe)
                else:
                    pdf.ln(4)
            pdf.output(str(pdf_path))
        except ImportError:
            return None
    return pdf_path


def write_cv_files(
    profile: Profile, target_role: str = "", fmt: str = "md"
) -> dict[str, Path]:
    md = build_cv_markdown(profile, target_role)
    slug = slugify(target_role or profile.headline or "general") or "general"
    out_dir = data_dir() / "cv"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"cv-{slug}.md"
    txt_path = out_dir / f"cv-{slug}.txt"
    md_path.write_text(md, encoding="utf-8")
    plain = (
        md.replace("# ", "")
        .replace("## ", "")
        .replace("### ", "")
        .replace("**", "")
        .replace("*", "")
    )
    txt_path.write_text(plain, encoding="utf-8")
    result: dict[str, Path] = {"markdown": md_path, "text": txt_path}
    if fmt == "pdf":
        pdf_path = write_cv_pdf(profile, target_role)
        if pdf_path:
            result["pdf"] = pdf_path
    return result
