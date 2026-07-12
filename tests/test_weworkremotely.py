"""We Work Remotely scraper offline path."""

from __future__ import annotations

from nerajob.scrapers.registry import available_scrapers
from nerajob.scrapers.weworkremotely import WeWorkRemotelyScraper


def test_wwr_offline_forced(monkeypatch) -> None:
    monkeypatch.setenv("NERAJOB_WWR_OFFLINE", "1")
    jobs = WeWorkRemotelyScraper().search("python", limit=5)
    assert jobs
    assert all(j.source == "weworkremotely" for j in jobs)
    assert any("python" in " ".join(j.tags).lower() or "python" in j.title.lower() for j in jobs)


def test_wwr_in_registry() -> None:
    scrapers = available_scrapers()
    assert "weworkremotely" in scrapers
