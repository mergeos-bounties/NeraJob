"""Export saved jobs to CSV for spreadsheet review."""

from __future__ import annotations

import csv
from pathlib import Path

from nerajob.models import JobPosting


def jobs_to_csv(jobs: list[JobPosting], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["id", "source", "title", "company", "location", "remote", "url", "tags", "salary"]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for j in jobs:
            w.writerow(
                {
                    "id": j.id,
                    "source": j.source,
                    "title": j.title,
                    "company": j.company,
                    "location": j.location,
                    "remote": j.remote,
                    "url": j.url,
                    "tags": "|".join(j.tags or []),
                    "salary": j.salary or "",
                }
            )
    return out_path
