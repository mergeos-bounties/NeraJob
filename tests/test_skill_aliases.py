from nerajob.match import SKILL_ALIASES, expand_skills


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


def test_expand_skills_education_and_edtech():
    lms = expand_skills({"lms"})
    assert "education" in lms
    assert "curriculum" in lms
    assert "assessment" in lms

    tutoring = expand_skills({"tutoring"})
    assert "edtech" in tutoring
    assert "learning management system" in tutoring
    assert "instructional design" in tutoring
