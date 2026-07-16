import json

from typer.testing import CliRunner

from nerajob.cli import app
from nerajob.match import SKILL_ALIASES, expand_skills, extract_skills_from_text


def test_expand_skills_python_aliases():
    out = expand_skills({"python"})
    assert "django" in out
    assert "fastapi" in out
    assert "python" in out


def test_expand_skills_devops():
    out = expand_skills({"k8s"})
    assert "kubernetes" in out or "devops" in out
    assert SKILL_ALIASES


def test_expand_skills_rust_and_go():
    rust = expand_skills({"rust"})
    assert "cargo" in rust
    assert "tokio" in rust
    go = expand_skills({"golang"})
    assert "go" in go
    assert "gin" in go


def test_expand_skills_sql_and_cloud():
    sql = expand_skills({"postgres"})
    assert "sql" in sql
    assert "database" in sql
    cloud = expand_skills({"aws"})
    assert "cloud" in cloud
    assert "lambda" in cloud


def test_expand_skills_java_kotlin():
    java = expand_skills({"java"})
    assert "spring" in java
    assert "jvm" in java
    kotlin = expand_skills({"kotlin"})
    assert "java" in kotlin
    assert "maven" in kotlin


def test_expand_skills_mobile():
    mob = expand_skills({"flutter"})
    assert "mobile" in mob
    assert "android" in mob
    ios = expand_skills({"ios"})
    assert "mobile" in ios
    assert "swift" in ios


def test_extract_skills_from_text_expands_alias_groups():
    text = (
        "Built Django APIs with PostgreSQL, Kubernetes, React dashboards, "
        "and PyTorch NLP tooling."
    )
    matches = extract_skills_from_text(text)
    assert matches["python"] == ["django"]
    assert matches["sql"] == ["postgresql"]
    assert matches["devops"] == ["kubernetes"]
    assert matches["javascript"] == ["react"]
    assert matches["ml_ai"] == ["nlp", "pytorch"]


def test_extract_skills_from_text_uses_token_boundaries():
    matches = extract_skills_from_text("Django engineer who ships reliable APIs")
    assert "go" not in matches


def test_skills_extract_cli_reads_text_fixture():
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "skills",
            "extract",
            "--text-file",
            "data/samples/resume_skills.txt",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert {"python", "sql", "devops", "javascript"}.issubset(set(payload["skills"]))
    assert payload["matches"]["python"] == ["django"]
    assert "fastapi" in payload["expanded"]["python"]
