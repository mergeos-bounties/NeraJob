"""Tests for scan preset profile."""

from pathlib import Path

from nerajob.models import ScanPreset
from nerajob.storage import load_scan_preset, save_scan_preset


def test_scan_preset_defaults():
    preset = ScanPreset()
    assert preset.remote_only is False
    assert preset.skill_filters == []
    assert preset.min_score == 0.0
    assert preset.min_salary == 0
    assert preset.max_results == 20


def test_scan_perset_roundtrip(tmp_path: Path) -> None:
    from nerajob import config as cfg

    original = cfg.SCAN_PRESET_PATH
    try:
        cfg.SCAN_PRESET_PATH = tmp_path / "scan-preset.json"
        preset = ScanPreset(remote_only=True, skill_filters=["python"], min_score=30.0)
        save_scan_preset(preset)
        loaded = load_scan_preset()
        assert loaded.remote_only is True
        assert loaded.skill_filters == ["python"]
        assert loaded.min_score == 30.0
    finally:
        cfg.SCAN_PRESET_PATH = original
