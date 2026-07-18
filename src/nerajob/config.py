from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    raw = os.getenv("NERAJOB_DATA_DIR", "data")
    path = Path(raw)
    if not path.is_absolute():
        path = project_root() / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def user_agent() -> str:
    return os.getenv(
        "NERAJOB_USER_AGENT",
        "NeraJob/0.1 (+https://github.com/mergeos-bounties/NeraJob)",
    )


def http_timeout() -> float:
    try:
        return float(os.getenv("NERAJOB_HTTP_TIMEOUT", "20"))
    except ValueError:
        return 20.0


PROFILE_PATH = data_dir() / "profile.json"
JOBS_PATH = data_dir() / "jobs.json"
APPLICATIONS_DIR = data_dir() / "applications"
SCAN_PRESET_PATH = data_dir() / "scan-preset.json"
