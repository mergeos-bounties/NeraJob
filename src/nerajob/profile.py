"""User profile and preset management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nerajob.config import CONFIG_DIR


def profiles_dir() -> Path:
    p = CONFIG_DIR / "profiles"
    p.mkdir(parents=True, exist_ok=True)
    return p


def list_profiles() -> list[dict]:
    profiles = []
    for f in sorted(profiles_dir().glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["_name"] = f.stem
            profiles.append(data)
        except (json.JSONDecodeError, OSError):
            pass
    return profiles


def save_profile(name: str, remote_only: bool = False, skills: list[str] | None = None) -> Path:
    path = profiles_dir() / f"{name}.json"
    data = {
        "remote_only": remote_only,
        "skills": skills or [],
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def load_profile(name: str) -> dict[str, Any]:
    path = profiles_dir() / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Profile '{name}' not found")
    return json.loads(path.read_text(encoding="utf-8"))


def default_profile() -> dict[str, Any]:
    for p in list_profiles():
        return p
    return {"remote_only": False, "skills": []}
