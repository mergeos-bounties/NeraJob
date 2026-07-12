"""Capture NeraJob Qt GUI screenshots into docs/screenshots/."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from nerajob.gui.main_window import MainWindow
    from nerajob.scrapers.registry import get_scraper
    from nerajob.storage import upsert_jobs

    # seed sample jobs
    upsert_jobs(get_scraper("sample").search(query="python", location="remote", limit=10))

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.processEvents()

    shots = [
        ("gui-scan.png", "scan"),
        ("gui-jobs.png", "jobs"),
        ("gui-profile.png", "profile"),
        ("gui-cv.png", "cv"),
        ("gui-apply.png", "apply"),
    ]

    def grab_all(i: int = 0) -> None:
        if i >= len(shots):
            app.quit()
            return
        name, page = shots[i]
        win._goto(page)
        if page == "scan":
            win.do_scan()
        app.processEvents()
        path = OUT / name
        win.grab().save(str(path), "PNG")
        print("wrote", path, path.stat().st_size)
        QTimer.singleShot(200, lambda: grab_all(i + 1))

    QTimer.singleShot(300, grab_all)
    app.exec()


if __name__ == "__main__":
    main()
