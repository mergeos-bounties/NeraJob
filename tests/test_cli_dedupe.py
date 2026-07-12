"""Tests for the CLI dedupe logic."""
import pytest
from datetime import datetime, timezone
from nerajob.cli import _dedupe_jobs
from nerajob.models import JobPosting


def _job(id: str, title: str, company: str, url: str = "") -> JobPosting:
    return JobPosting(
        id=id,
        source="test",
        title=title,
        company=company,
        location="Remote",
        url=url,
        description="desc",
        tags=[],
        remote=True,
        scraped_at=datetime.now(timezone.utc).isoformat(),
    )


def test_dedupe_exact_url_match():
    a = _job("a", "Senior Python Engineer", "PyTech", "https://example.com/job/1")
    b = _job("b", "Senior Python Engineer", "PyTech", "https://example.com/job/1")
    c = _job("c", "Python Engineer", "PyTech GmbH", "https://example.com/job/2")

    unique, total, dupes = _dedupe_jobs([a, b, c])
    assert total == 3
    assert len(unique) == 2
    assert dupes == 1
    assert unique[0].id == "a"
    assert unique[1].id == "c"


def test_dedupe_by_title_company_when_no_url():
    a = _job("a", "Backend Engineer", "Acme", "")
    b = _job("b", "Backend Engineer", "Acme", "")
    c = _job("c", "Backend Engineer", "Acme", "https://example.com/job/3")

    unique, total, dupes = _dedupe_jobs([a, b, c])
    assert total == 3
    assert len(unique) == 2
    assert dupes == 1
    # c has URL, so it will be kept
    assert unique[-1].id == "c"


def test_dedupe_title_company_case_insensitive():
    a = _job("a", "Backend Engineer", "Acme", "")
    b = _job("b", "backend engineer", "acme", "")
    c = _job("c", "BACKEND ENGINEER", "ACME", "https://x.com/1")

    unique, total, dupes = _dedupe_jobs([a, b, c])
    assert total == 3
    assert len(unique) == 2
    assert dupes == 1


def test_dedupe_empty_list():
    unique, total, dupes = _dedupe_jobs([])
    assert unique == []
    assert total == 0
    assert dupes == 0


def test_dedupe_no_duplicates():
    a = _job("a", "Backend", "Acme", "https://a.com")
    b = _job("b", "Frontend", "Beta", "https://b.com")
    c = _job("c", "DevOps", "Gamma", "https://c.com")

    unique, total, dupes = _dedupe_jobs([a, b, c])
    assert total == 3
    assert len(unique) == 3
    assert dupes == 0


def test_dedupe_preserves_order():
    """First occurrence wins in dedupe."""
    a = _job("a", "Python Dev", "Acme", "https://acme.io/job")
    b = _job("b", "Python Dev", "Acme", "https://acme.io/JOB")  # lowercased to same as a
    c = _job("c", "Python Dev", "Acme", "https://acme.io/role")  # different URL

    unique, total, dupes = _dedupe_jobs([a, b, c])
    # URLs are lowercased, so a and b are same key; a wins, b is dupe
    # c has a different URL, so it wins
    assert len(unique) == 2
    assert dupes == 1
    assert unique[0].id == "a"
    assert unique[1].id == "c"


def test_dedupe_keeps_jobs_without_url():
    a = _job("a", "Unique Role", "Company A", "")
    b = _job("b", "Unique Role", "Company A", "")

    unique, total, dupes = _dedupe_jobs([a, b])
    assert total == 2
    assert len(unique) == 1
    assert dupes == 1