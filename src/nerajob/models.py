from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Experience(BaseModel):
    title: str
    company: str
    start: str = ""
    end: str = "Present"
    highlights: list[str] = Field(default_factory=list)


class Education(BaseModel):
    school: str
    degree: str = ""
    year: str = ""


class Profile(BaseModel):
    full_name: str = "Your Name"
    email: str = "you@example.com"
    phone: str = ""
    location: str = "Remote"
    headline: str = "Software Engineer"
    summary: str = "Results-driven engineer building reliable products."
    skills: list[str] = Field(default_factory=lambda: ["Python", "APIs", "SQL"])
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=lambda: ["English"])


class JobPosting(BaseModel):
    id: str
    source: str
    title: str
    company: str
    location: str = "Remote"
    url: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    salary: str = ""
    remote: bool = True
    scraped_at: str = Field(default_factory=utc_now_iso)
    raw: dict[str, Any] = Field(default_factory=dict)


class ScanPreset(BaseModel):
    remote_only: bool = False
    skill_filters: list[str] = Field(default_factory=list)
    min_score: float = 0.0
    min_salary: int = 0
    max_results: int = 20


class ApplicationPackage(BaseModel):
    job_id: str
    created_at: str = Field(default_factory=utc_now_iso)
    cover_note: str = ""
    checklist: list[str] = Field(default_factory=list)
    cv_markdown_path: str = ""
    notes: str = ""


def parse_salary_value(salary: str) -> int | None:
    """Extract a numeric annual salary floor from a salary string. Returns None if unparseable."""
    import re
    if not salary or not salary.strip():
        return None
    s = salary.lower().replace(",", "").replace("€", "").replace("$", "").replace("£", "").strip()
    # Try ranges like "80k-120k" or "80k – 120k"
    m = re.search(r"(\d+)\s*k", s)
    if m:
        return int(m.group(1)) * 1000
    # Try "80000-120000"
    m = re.search(r"(\d{4,6})", s)
    if m:
        val = int(m.group(1))
        # If first number looks like annual salary
        if 10000 <= val <= 999999:
            return val
    return None
