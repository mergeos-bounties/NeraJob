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
