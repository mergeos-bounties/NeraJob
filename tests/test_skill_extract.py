"""Tests for offline skill extraction from plain text."""

from pathlib import Path

from nerajob.match import extract_skills_from_text


def test_extract_skills_from_python_text():
    text = "Expert in Python, Django, and FastAPI. Experience with PostgreSQL."
    result = extract_skills_from_text(text)
    assert "python" in result
    assert "django" in result["python"]
    assert "fastapi" in result["python"]
    assert "sql" in result
    assert "postgres" in result["sql"] or "postgresql" in result["sql"]


def test_extract_skills_from_devops_text():
    text = "DevOps engineer with Docker, Kubernetes, Terraform, and CI/CD."
    result = extract_skills_from_text(text)
    assert "devops" in result
    assert "docker" in result["devops"]
    assert "kubernetes" in result["devops"]
    assert "terraform" in result["devops"]


def test_extract_skills_from_full_resume():
    text = """Senior Python Backend Engineer

Experience with FastAPI, Django, and PostgreSQL.
Cloud infrastructure on AWS with Lambda and S3.
Containerized with Docker and Kubernetes."""
    result = extract_skills_from_text(text)
    assert "python" in result
    assert "sql" in result
    assert "cloud" in result
    assert "devops" in result


def test_extract_skills_no_match():
    text = "I enjoy long walks on the beach and reading books."
    result = extract_skills_from_text(text)
    assert result == {}


def test_extract_skills_multiword_alias():
    text = "Experienced with infrastructure as code and continuous integration."
    result = extract_skills_from_text(text)
    devops = result.get("devops", set())
    assert "infrastructure as code" in devops or "iac" in devops


def test_extract_skills_case_insensitive():
    text = "PYTHON DJANGO KUBERNETES"
    result = extract_skills_from_text(text)
    assert "python" in result
    assert "devops" in result


def test_extract_skills_with_textfile(tmp_path: Path) -> None:
    txt = tmp_path / "resume.txt"
    txt.write_text("Python developer with Flask and MongoDB experience.", encoding="utf-8")
    result = extract_skills_from_text(txt.read_text(encoding="utf-8"))
    assert "python" in result
    assert "flask" in result["python"]
