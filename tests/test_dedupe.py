"""Tests for deduplication."""

import pytest

from nerajob.dedupe import dedupe, dedupe_report


class TestDedupe:
    def test_empty(self):
        assert dedupe([]) == []

    def test_single(self):
        jobs = [{"url": "https://example.com/job/1", "title": "Engineer", "company": "Acme"}]
        assert dedupe(jobs) == jobs

    def test_duplicate_url(self):
        jobs = [
            {"url": "https://example.com/job/1", "title": "Engineer", "company": "Acme"},
            {"url": "https://example.com/job/1", "title": "Engineer", "company": "Acme"},
        ]
        result = dedupe(jobs)
        assert len(result) == 1

    def test_duplicate_title_company(self):
        jobs = [
            {"title": "Engineer", "company": "Acme"},
            {"title": "Engineer", "company": "Acme"},
        ]
        result = dedupe(jobs)
        assert len(result) == 1

    def test_different_urls(self):
        jobs = [
            {"url": "https://a.com/1", "title": "Engineer", "company": "Acme"},
            {"url": "https://b.com/2", "title": "Designer", "company": "Beta"},
        ]
        result = dedupe(jobs)
        assert len(result) == 2

    def test_url_preferred_over_title(self):
        jobs = [
            {"url": "https://a.com/1", "title": "Engineer", "company": "Acme"},
            {"url": "https://b.com/2", "title": "Engineer", "company": "Acme"},
        ]
        result = dedupe(jobs)
        assert len(result) == 2


class TestDedupeReport:
    def test_report_counts(self):
        jobs = [
            {"url": "https://a.com/1", "title": "Engineer", "company": "A"},
            {"url": "https://a.com/1", "title": "Engineer", "company": "A"},
            {"title": "Designer", "company": "B"},
            {"title": "Designer", "company": "B"},
        ]
        report = dedupe_report(jobs)
        assert report["total"] == 4
        assert report["unique"] == 2
        assert report["duplicates_removed"] == 2
