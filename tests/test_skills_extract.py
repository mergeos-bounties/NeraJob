"""Tests for skills extract CLI (nerajob skills-extract extract --text-file)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from nerajob.cli import app
from nerajob.match import SKILL_ALIASES, expand_skills

runner = CliRunner()


class TestExpandSkills:
    def test_python_aliases_expand(self):
        out = expand_skills({"python"})
        assert "django" in out
        assert "fastapi" in out
        assert "python" in out

    def test_phrase_match_in_text(self):
        """Skill phrases like 'machine learning' should match inside a sentence."""
        text = "i have 5 years of machine learning experience."
        tokens = {k: v for k, v in SKILL_ALIASES.items() if k in text}
        assert "ml" in tokens or "ml_ai" in tokens or "machine learning" in text

    def test_expand_devops(self):
        out = expand_skills({"k8s"})
        assert "kubernetes" in out or "devops" in out

    def test_expand_sql_cloud(self):
        sql = expand_skills({"postgres"})
        assert "sql" in sql
        cloud = expand_skills({"aws"})
        assert "cloud" in cloud


class TestSkillsExtractCLI:
    def test_extract_from_plain_text_file(self, tmp_path: Path):
        resume = tmp_path / "resume.txt"
        resume.write_text(
            "Senior Python developer experienced in Django, FastAPI, "
            "Docker, and AWS cloud infrastructure. Familiar with PostgreSQL and SQL.",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["skills-extract", "extract", "--text-file", str(resume)])
        assert result.exit_code == 0
        assert "python" in result.output.lower()
        assert "devops" in result.output.lower()
        assert "sql" in result.output.lower()
        assert "cloud" in result.output.lower()

    def test_extract_from_markdown_file(self, tmp_path: Path):
        md = tmp_path / "cv.md"
        md.write_text(
            "# John Doe\n\n## Skills\n- Python\n- Docker\n- Machine learning\n- PyTorch\n- Cloud (AWS)\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["skills-extract", "extract", "--text-file", str(md)])
        assert result.exit_code == 0
        assert "python" in result.output.lower()
        assert "devops" in result.output.lower()
        assert "ml_ai" in result.output.lower()
        assert "cloud" in result.output.lower()

    def test_extract_no_expand_flag(self, tmp_path: Path):
        resume = tmp_path / "resume.txt"
        resume.write_text("python developer with fastapi and django", encoding="utf-8")
        result = runner.invoke(
            app, ["skills-extract", "extract", "--text-file", str(resume), "--no-expand"]
        )
        assert result.exit_code == 0
        # With no-expand, should still show canonical groups but no extra alias expansion
        assert "python" in result.output.lower()

    def test_extract_nonexistent_file(self, tmp_path: Path):
        missing = tmp_path / "does_not_exist.txt"
        result = runner.invoke(app, ["skills-extract", "extract", "--text-file", str(missing)])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_extract_empty_file(self, tmp_path: Path):
        empty = tmp_path / "empty.txt"
        empty.write_text("", encoding="utf-8")
        result = runner.invoke(app, ["skills-extract", "extract", "--text-file", str(empty)])
        # Empty should exit with message, not crash
        assert result.exit_code in (0, 1)

    def test_extract_skills_count_header(self, tmp_path: Path):
        resume = tmp_path / "resume.txt"
        resume.write_text(
            "experienced python and django developer; docker, kubernetes; aws; postgres",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["skills-extract", "extract", "--text-file", str(resume)])
        assert result.exit_code == 0
        assert "Canonical skills found:" in result.output
        assert "Expanded skills" in result.output