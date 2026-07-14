"""Tests for #36: min-salary filter on scan."""
from __future__ import annotations

from nerajob.models import parse_salary_value


def test_parse_salary_k_range() -> None:
    assert parse_salary_value("80k-120k") == 80000
    assert parse_salary_value("80k – 120k") == 80000
    assert parse_salary_value("80K-120K") == 80000


def test_parse_salary_numeric_range() -> None:
    assert parse_salary_value("80000-120000") == 80000
    assert parse_salary_value("$80,000 - $120,000") == 80000


def test_parse_salary_single_value() -> None:
    assert parse_salary_value("€55,000") == 55000
    assert parse_salary_value("55000") == 55000


def test_parse_salary_empty() -> None:
    assert parse_salary_value("") is None
    assert parse_salary_value("  ") is None


def test_parse_salary_unparseable() -> None:
    assert parse_salary_value("competitive") is None
    assert parse_salary_value("negotiable") is None
