from nerajob.cv.builder import build_cv_markdown, write_cv_files
from nerajob.storage import default_profile
import os


def test_build_cv_contains_name_and_skills():
    profile = default_profile()
    md = build_cv_markdown(profile, target_role="Python Engineer")
    assert profile.full_name in md
    assert "Python" in md
    assert "Python Engineer" in md


def test_write_cv_files_default_formats(tmp_path, monkeypatch):
    # Use a temporary directory for data_dir
    from nerajob.config import data_dir
    # We'll monkeypatch data_dir to return a temporary path
    tmp_cv_dir = tmp_path / "cv"
    tmp_cv_dir.mkdir()
    # We need to monkeypatch the data_dir function in the module where it's used
    # Since data_dir is imported from nerajob.config, we can monkeypatch that module
    import nerajob.config
    original_data_dir = nerajob.config.data_dir
    nerajob.config.data_dir = lambda: tmp_cv_dir
    try:
        profile = default_profile()
        result = write_cv_files(profile, target_role="Test")
        # Expect markdown and text
        assert result["markdown"] is not None
        assert result["text"] is not None
        assert result["markdown"].exists()
        assert result["text"].exists()
        # Check content
        md_content = result["markdown"].read_text(encoding="utf-8")
        assert profile.full_name in md_content
        assert "Test" in md_content
        txt_content = result["text"].read_text(encoding="utf-8")
        assert profile.full_name in txt_content
        # PDF not requested
        assert result.get("pdf") is None
    finally:
        nerajob.config.data_dir = original_data_dir


def test_write_cv_files_with_pdf(tmp_path, monkeypatch):
    from nerajob.config import data_dir
    tmp_cv_dir = tmp_path / "cv"
    tmp_cv_dir.mkdir()
    import nerajob.config
    original_data_dir = nerajob.config.data_dir
    nerajob.config.data_dir = lambda: tmp_cv_dir
    try:
        profile = default_profile()
        result = write_cv_files(profile, target_role="PDF Test", formats=["markdown", "text", "pdf"])
        assert result["markdown"] is not None
        assert result["text"] is not None
        assert result["pdf"] is not None
        assert result["pdf"].exists()
        # Check that PDF is not empty
        assert result["pdf"].stat().st_size > 0
    finally:
        nerajob.config.data_dir = original_data_dir
