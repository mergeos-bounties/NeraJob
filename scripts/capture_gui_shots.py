"""Capture NeraJob Qt GUI screenshots into docs/screenshots/ with readable fonts."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

# Prefer software raster for deterministic screenshots (avoid GPU font bugs)
os.environ.setdefault("QT_OPENGL", "software")
os.environ.setdefault("QT_QUICK_BACKEND", "software")


def main() -> None:
    from PySide6.QtCore import QTimer, Qt
    from PySide6.QtGui import QFont, QGuiApplication
    from PySide6.QtWidgets import QApplication

    from nerajob.gui.main_window import MainWindow
    from nerajob.scrapers.registry import get_scraper
    from nerajob.storage import upsert_jobs

    # seed sample jobs for job board preview
    upsert_jobs(get_scraper("sample").search(query="python", location="remote", limit=10))

    app = QApplication(sys.argv)
    app.setApplicationName("NeraJob")
    app.setFont(QFont("Segoe UI", 10))

    win = MainWindow()
    win.setWindowTitle("NeraJob · screenshot")
    win.resize(1280, 800)
    win.show()
    # Force a paint cycle after show
    for _ in range(5):
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
        if page == "jobs":
            win.refresh_jobs_table()
        # Allow layout + font shaping to settle
        for _ in range(8):
            app.processEvents()
        path = OUT / name
        # High-DPI aware grab of the window frame
        pix = win.grab()
        if pix.isNull():
            screen = QGuiApplication.primaryScreen()
            if screen is not None:
                pix = screen.grabWindow(int(win.winId()))
        ok = pix.save(str(path), "PNG")
        print("wrote", path, path.stat().st_size if path.exists() else 0, "ok=" + str(ok))
        QTimer.singleShot(350, lambda: grab_all(i + 1))

    QTimer.singleShot(500, grab_all)
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
