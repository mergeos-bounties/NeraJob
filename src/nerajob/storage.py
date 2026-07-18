from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from nerajob.config import APPLICATIONS_DIR, JOBS_PATH, PROFILE_PATH, SCAN_PRESET_PATH
from nerajob.models import ApplicationPackage, Education, Experience, JobPosting, Profile, ScanPreset


def _read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_profile() -> Profile | None:
    if not PROFILE_PATH.exists():
        return None
    return Profile.model_validate(_read_json(PROFILE_PATH, {}))


def save_profile(profile: Profile) -> Path:
    _write_json(PROFILE_PATH, profile.model_dump())
    return PROFILE_PATH


def default_profile() -> Profile:
    return Profile(
        experience=[
            Experience(
                title="Software Engineer",
                company="Example Co",
                start="2022",
                end="Present",
                highlights=[
                    "Built APIs and automation used by product teams",
                    "Improved reliability and delivery speed",
                ],
            )
        ],
        education=[
            Education(
                school="University",
                degree="B.S. Computer Science",
                year="2021",
            )
        ],
        links=["https://github.com/your-handle", "https://linkedin.com/in/your-handle"],
    )


def load_jobs() -> list[JobPosting]:
    raw = _read_json(JOBS_PATH, [])
    return [JobPosting.model_validate(item) for item in raw]


def save_jobs(jobs: Iterable[JobPosting]) -> Path:
    payload = [job.model_dump() for job in jobs]
    _write_json(JOBS_PATH, payload)
    return JOBS_PATH


def upsert_jobs(new_jobs: Iterable[JobPosting]) -> list[JobPosting]:
    by_id = {job.id: job for job in load_jobs()}
    for job in new_jobs:
        by_id[job.id] = job
    merged = sorted(by_id.values(), key=lambda j: j.scraped_at, reverse=True)
    save_jobs(merged)
    return merged


def get_job(job_id: str) -> JobPosting | None:
    for job in load_jobs():
        if job.id == job_id:
            return job
    return None


def load_scan_preset() -> ScanPreset:
    return ScanPreset.model_validate(_read_json(SCAN_PRESET_PATH, {}))


def save_scan_preset(preset: ScanPreset) -> Path:
    _write_json(SCAN_PRESET_PATH, preset.model_dump())
    return SCAN_PRESET_PATH


def save_application(package: ApplicationPackage) -> Path:
    APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = APPLICATIONS_DIR / f"{package.job_id}.json"
    _write_json(path, package.model_dump())
    return path
