"""Tests for profile/preset management."""

import json
from pathlib import Path

import pytest

from nerajob.profile import save_profile, load_profile, list_profiles, profiles_dir


class TestProfile:
    def test_save_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setattr("nerajob.profile.profiles_dir", lambda: tmp_path)
        save_profile("test", remote_only=True, skills=["python"])
        data = load_profile("test")
        assert data["remote_only"] is True
        assert data["skills"] == ["python"]

    def test_list_profiles(self, tmp_path, monkeypatch):
        monkeypatch.setattr("nerajob.profile.profiles_dir", lambda: tmp_path)
        save_profile("a", remote_only=True)
        save_profile("b", remote_only=False, skills=["js"])
        profiles = list_profiles()
        assert len(profiles) == 2

    def test_load_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            load_profile("nonexistent")
