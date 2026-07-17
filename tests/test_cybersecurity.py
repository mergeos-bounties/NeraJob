"""Tests for cybersecurity skill aliases."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nerajob.match import expand_skills


def test_expand_skills_cybersecurity():
    """Test cybersecurity alias expansion."""
    out = expand_skills({"cybersecurity"})
    assert "cybersecurity" in out
    assert "security" in out
    assert "soc" in out
    assert "siem" in out
    assert "pentest" in out
    assert "iam" in out
    assert "infosec" in out


def test_expand_skills_siem():
    """Test SIEM alias expansion."""
    out = expand_skills({"siem"})
    assert "cybersecurity" in out
    assert "soc" in out
    assert "security" in out


def test_expand_skills_pentest():
    """Test pentest alias expansion."""
    out = expand_skills({"pentest"})
    assert "cybersecurity" in out
    assert "security" in out
    assert "infosec" in out


def test_expand_skills_iam():
    """Test IAM alias expansion."""
    out = expand_skills({"iam"})
    assert "cybersecurity" in out
    assert "security" in out
    assert "infosec" in out


def test_expand_skills_infosec():
    """Test infosec alias expansion."""
    out = expand_skills({"infosec"})
    assert "cybersecurity" in out
    assert "security" in out
    assert "iam" in out


def test_expand_skills_soc():
    """Test SOC alias expansion."""
    out = expand_skills({"soc"})
    assert "cybersecurity" in out
    assert "security" in out
    assert "siem" in out


if __name__ == "__main__":
    test_expand_skills_cybersecurity()
    test_expand_skills_siem()
    test_expand_skills_pentest()
    test_expand_skills_iam()
    test_expand_skills_infosec()
    test_expand_skills_soc()
    print("✅ All cybersecurity tests passed!")
