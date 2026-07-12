from pathlib import Path

from nerajob.export_jobs import jobs_to_csv
from nerajob.models import JobPosting


def test_jobs_csv(tmp_path: Path) -> None:
    jobs = [
        JobPosting(
            id="1",
            source="sample",
            title="Python Eng",
            company="Acme",
            tags=["python"],
            remote=True,
        )
    ]
    path = jobs_to_csv(jobs, tmp_path / "j.csv")
    text = path.read_text(encoding="utf-8")
    assert "Python Eng" in text
    assert "sample" in text
