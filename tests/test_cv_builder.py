
from nerajob.cv.builder import build_cv_markdown, write_cv_files, write_cv_pdf
from nerajob.storage import default_profile


def test_build_cv_contains_name_and_skills():
    profile = default_profile()
    md = build_cv_markdown(profile, target_role="Python Engineer")
    assert profile.full_name in md
    assert "Python" in md
    assert "Python Engineer" in md


def test_write_cv_files_md_format():
    profile = default_profile()
    result = write_cv_files(profile, fmt="md")
    assert "markdown" in result
    assert "text" in result
    assert result["markdown"].suffix == ".md"
    assert result["text"].suffix == ".txt"
    assert result["markdown"].exists()
    assert result["text"].exists()


def test_write_cv_files_pdf_format_fallback_gracefully(monkeypatch):
    import builtins

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in ("weasyprint", "fpdf"):
            raise ImportError(f"No module named {name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    profile = default_profile()
    result = write_cv_files(profile, fmt="pdf")
    assert "markdown" in result
    assert "text" in result
    assert "pdf" not in result
    assert result["markdown"].exists()


def test_write_cv_pdf_returns_none_when_missing_deps(monkeypatch):
    import builtins

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in ("weasyprint", "fpdf"):
            raise ImportError(f"No module named {name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    profile = default_profile()
    pdf_path = write_cv_pdf(profile)
    assert pdf_path is None
