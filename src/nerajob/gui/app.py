"""Entry: nerajob-gui / python -m nerajob.gui.app"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("Install GUI extras: pip install -e \".[gui]\"  (needs PySide6)", file=sys.stderr)
        return 1
    from nerajob.gui.main_window import MainWindow

    app = QApplication(sys.argv if argv is None else argv)
    app.setApplicationName("NeraJob")
    app.setOrganizationName("MergeOS")
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
