"""NeraJob modern desktop shell (PySide6)."""

from __future__ import annotations


from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from nerajob import __version__
from nerajob.apply.assistant import prepare_application
from nerajob.cv.builder import write_cv_files
from nerajob.gui.styles import STYLESHEET
from nerajob.scrapers.registry import available_scrapers, get_scraper
from nerajob.storage import (
    default_profile,
    get_job,
    load_jobs,
    load_profile,
    save_profile,
    upsert_jobs,
)


def _card() -> QFrame:
    f = QFrame()
    f.setObjectName("card")
    return f


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"NeraJob · v{__version__}")
        self.resize(1180, 740)
        self.setMinimumSize(QSize(960, 600))
        self.setStyleSheet(STYLESHEET)

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- Sidebar ---
        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(220)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(16, 20, 16, 16)
        sl.setSpacing(6)
        brand = QLabel("NeraJob")
        brand.setObjectName("brand")
        sub = QLabel("Scan · CV · Apply")
        sub.setObjectName("brandSub")
        sl.addWidget(brand)
        sl.addWidget(sub)
        sl.addSpacing(18)

        self._nav_btns: list[QPushButton] = []
        for key, label in [
            ("scan", "🔍  Scan jobs"),
            ("jobs", "📋  Job board"),
            ("profile", "👤  Profile"),
            ("cv", "📄  Build CV"),
            ("apply", "🚀  Apply pack"),
        ]:
            b = QPushButton(label)
            b.setObjectName("nav")
            b.setProperty("class", "nav")
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda checked=False, k=key: self._goto(k))
            b.setStyleSheet(STYLESHEET)  # ensure class
            b.setProperty("class", "nav")
            # Qt stylesheets don't use class= like CSS for QPushButton easily —
            # we set objectName pattern via setProperty and use .nav in sheet as QPushButton.nav
            # Actually QSS uses class only if set with setProperty and unpolish - simpler: objectName
            b.setObjectName("navBtn")
            self._nav_btns.append(b)
            sl.addWidget(b)

        # Fix nav styling: use setProperty with class selector needs polish
        for b in self._nav_btns:
            b.setProperty("class", "nav")
            b.setStyleSheet(
                "QPushButton { text-align: left; padding: 12px 14px; border: none; "
                "border-radius: 10px; background: transparent; color: #94a3b8; font-weight: 600; }"
                "QPushButton:hover { background: #1e293b; color: #e2e8f0; }"
                "QPushButton:checked { background: #0e7490; color: #ecfeff; }"
            )

        sl.addStretch(1)
        ver = QLabel(f"v{__version__} · local-first")
        ver.setObjectName("brandSub")
        sl.addWidget(ver)
        root.addWidget(side)

        # --- Pages ---
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.pages = {
            "scan": self._build_scan_page(),
            "jobs": self._build_jobs_page(),
            "profile": self._build_profile_page(),
            "cv": self._build_cv_page(),
            "apply": self._build_apply_page(),
        }
        self._page_keys = list(self.pages.keys())
        for w in self.pages.values():
            self.stack.addWidget(w)

        sb = QStatusBar()
        self.setStatusBar(sb)
        self._status("Ready · offline sample source works without network")
        self._goto("scan")
        self.refresh_jobs_table()

    def _status(self, msg: str) -> None:
        self.statusBar().showMessage(msg)

    def _goto(self, key: str) -> None:
        idx = self._page_keys.index(key)
        self.stack.setCurrentIndex(idx)
        for i, b in enumerate(self._nav_btns):
            b.setChecked(i == idx)

    # ----- Scan -----
    def _build_scan_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)
        title = QLabel("Scan job sources")
        title.setObjectName("h1")
        lay.addWidget(title)
        sub = QLabel("Pull listings from registered scrapers into your local jobs cache.")
        sub.setObjectName("h2")
        lay.addWidget(sub)

        card = _card()
        fl = QFormLayout(card)
        fl.setContentsMargins(20, 20, 20, 20)
        fl.setSpacing(12)
        self.scan_query = QLineEdit()
        self.scan_query.setPlaceholderText("python backend")
        self.scan_query.setText("python")
        self.scan_loc = QLineEdit()
        self.scan_loc.setPlaceholderText("remote / city")
        self.scan_loc.setText("remote")
        self.scan_source = QComboBox()
        self.scan_source.addItems(sorted(available_scrapers().keys()))
        if self.scan_source.findText("sample") >= 0:
            self.scan_source.setCurrentText("sample")
        self.scan_limit = QSpinBox()
        self.scan_limit.setRange(1, 100)
        self.scan_limit.setValue(20)
        fl.addRow("Keywords", self.scan_query)
        fl.addRow("Location", self.scan_loc)
        fl.addRow("Source", self.scan_source)
        fl.addRow("Limit", self.scan_limit)
        lay.addWidget(card)

        row = QHBoxLayout()
        btn = QPushButton("Run scan")
        btn.setProperty("class", "primary")
        btn.setStyleSheet(
            "QPushButton { background: #06b6d4; color: #042f2e; border: none; border-radius: 10px; "
            "padding: 10px 18px; font-weight: 700; } QPushButton:hover { background: #22d3ee; }"
        )
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self.do_scan)
        row.addWidget(btn)
        btn_all = QPushButton("Scan all sources")
        btn_all.setStyleSheet(
            "QPushButton { background: #1e293b; border: 1px solid #334155; border-radius: 10px; "
            "padding: 10px 16px; color: #e2e8f0; font-weight: 600; }"
        )
        btn_all.clicked.connect(self.do_scan_all)
        row.addWidget(btn_all)
        row.addStretch(1)
        lay.addLayout(row)
        self.scan_log = QTextEdit()
        self.scan_log.setReadOnly(True)
        self.scan_log.setMinimumHeight(180)
        lay.addWidget(self.scan_log, 1)
        return page

    def do_scan(self) -> None:
        self._run_scan([self.scan_source.currentText()])

    def do_scan_all(self) -> None:
        self._run_scan(list(available_scrapers().keys()))

    def _run_scan(self, names: list[str]) -> None:
        q = self.scan_query.text().strip()
        loc = self.scan_loc.text().strip()
        limit = self.scan_limit.value()
        lines = [f"Scanning {', '.join(names)} · q={q!r} · loc={loc!r} · n={limit}"]
        collected = []
        for name in names:
            try:
                sc = get_scraper(name)
                found = sc.search(query=q, location=loc, limit=limit)
                lines.append(f"  {name}: {len(found)} hits")
                collected.extend(found)
            except Exception as exc:  # noqa: BLE001
                lines.append(f"  {name}: error {exc}")
        if not collected and "sample" not in names:
            found = get_scraper("sample").search(query=q, location=loc, limit=limit)
            lines.append(f"  fallback sample: {len(found)} hits")
            collected.extend(found)
        merged = upsert_jobs(collected)
        lines.append(f"Saved. Total jobs in cache: {len(merged)}")
        self.scan_log.setPlainText("\n".join(lines))
        self.refresh_jobs_table()
        self._status(f"Scan done · {len(collected)} new/updated · {len(merged)} total")

    # ----- Jobs -----
    def _build_jobs_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Job board")
        title.setObjectName("h1")
        lay.addWidget(title)
        sub = QLabel("Local cache (data/jobs.json). Select a row to prepare an apply package.")
        sub.setObjectName("h2")
        lay.addWidget(sub)
        self.jobs_table = QTableWidget(0, 5)
        self.jobs_table.setHorizontalHeaderLabels(["ID", "Source", "Title", "Company", "Location"])
        self.jobs_table.horizontalHeader().setStretchLastSection(True)
        self.jobs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.jobs_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.jobs_table.setAlternatingRowColors(False)
        lay.addWidget(self.jobs_table, 1)
        btn = QPushButton("Refresh")
        btn.setStyleSheet(
            "QPushButton { background: #1e293b; border: 1px solid #334155; border-radius: 10px; "
            "padding: 8px 14px; }"
        )
        btn.clicked.connect(self.refresh_jobs_table)
        lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignLeft)
        return page

    def refresh_jobs_table(self) -> None:
        jobs = load_jobs()
        self.jobs_table.setRowCount(len(jobs))
        for r, job in enumerate(jobs):
            for c, val in enumerate(
                [job.id, job.source, job.title, job.company, job.location]
            ):
                self.jobs_table.setItem(r, c, QTableWidgetItem(str(val)))
        self.jobs_table.resizeColumnsToContents()

    # ----- Profile -----
    def _build_profile_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Profile")
        title.setObjectName("h1")
        lay.addWidget(title)
        card = _card()
        fl = QFormLayout(card)
        fl.setContentsMargins(20, 20, 20, 20)
        self.prof_name = QLineEdit()
        self.prof_title = QLineEdit()
        self.prof_email = QLineEdit()
        self.prof_summary = QTextEdit()
        self.prof_summary.setMinimumHeight(100)
        self.prof_skills = QLineEdit()
        self.prof_skills.setPlaceholderText("python, fastapi, postgres")
        fl.addRow("Full name", self.prof_name)
        fl.addRow("Headline", self.prof_title)
        fl.addRow("Email", self.prof_email)
        fl.addRow("Summary", self.prof_summary)
        fl.addRow("Skills", self.prof_skills)
        lay.addWidget(card)
        row = QHBoxLayout()
        b1 = QPushButton("Load / init")
        b1.clicked.connect(self.load_profile_ui)
        b2 = QPushButton("Save profile")
        b2.setStyleSheet(
            "QPushButton { background: #06b6d4; color: #042f2e; border: none; border-radius: 10px; "
            "padding: 10px 18px; font-weight: 700; }"
        )
        b2.clicked.connect(self.save_profile_ui)
        for b in (b1, b2):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            if b is b1:
                b.setStyleSheet(
                    "QPushButton { background: #1e293b; border: 1px solid #334155; border-radius: 10px; "
                    "padding: 10px 16px; }"
                )
            row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addStretch(1)
        self.load_profile_ui()
        return page

    def load_profile_ui(self) -> None:
        p = load_profile()
        if not p:
            p = default_profile()
            save_profile(p)
        self.prof_name.setText(getattr(p, "full_name", None) or getattr(p, "name", "") or "")
        # Profile model fields may vary
        data = p.model_dump() if hasattr(p, "model_dump") else {}
        self.prof_name.setText(str(data.get("full_name") or data.get("name") or self.prof_name.text()))
        self.prof_title.setText(str(data.get("headline") or data.get("title") or ""))
        self.prof_email.setText(str(data.get("email") or ""))
        self.prof_summary.setPlainText(str(data.get("summary") or ""))
        skills = data.get("skills") or []
        if isinstance(skills, list):
            self.prof_skills.setText(", ".join(str(s) for s in skills))
        else:
            self.prof_skills.setText(str(skills))
        self._status("Profile loaded")

    def save_profile_ui(self) -> None:
        p = load_profile() or default_profile()
        data = p.model_dump()
        # map common fields if present on model
        for key, val in [
            ("full_name", self.prof_name.text().strip()),
            ("name", self.prof_name.text().strip()),
            ("headline", self.prof_title.text().strip()),
            ("title", self.prof_title.text().strip()),
            ("email", self.prof_email.text().strip()),
            ("summary", self.prof_summary.toPlainText().strip()),
            (
                "skills",
                [s.strip() for s in self.prof_skills.text().split(",") if s.strip()],
            ),
        ]:
            if key in data or key in ("full_name", "headline", "email", "summary", "skills"):
                data[key] = val
        try:
            from nerajob.models import Profile

            profile = Profile.model_validate(data)
            save_profile(profile)
            self._status("Profile saved")
            QMessageBox.information(self, "NeraJob", "Profile saved to data/profile.json")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "NeraJob", f"Could not save profile: {exc}")

    # ----- CV -----
    def _build_cv_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Build CV")
        title.setObjectName("h1")
        lay.addWidget(title)
        card = _card()
        fl = QFormLayout(card)
        fl.setContentsMargins(20, 20, 20, 20)
        self.cv_target = QLineEdit("Backend Engineer")
        fl.addRow("Target role", self.cv_target)
        lay.addWidget(card)
        btn = QPushButton("Generate CV files")
        btn.setStyleSheet(
            "QPushButton { background: #06b6d4; color: #042f2e; border: none; border-radius: 10px; "
            "padding: 10px 18px; font-weight: 700; }"
        )
        btn.clicked.connect(self.do_cv)
        lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignLeft)
        self.cv_out = QTextEdit()
        self.cv_out.setReadOnly(True)
        lay.addWidget(self.cv_out, 1)
        return page

    def do_cv(self) -> None:
        try:
            profile = load_profile() or default_profile()
            paths = write_cv_files(profile, target_role=self.cv_target.text().strip() or "Engineer")
            msg = "\n".join(f"{k}: {v}" for k, v in paths.items()) if isinstance(paths, dict) else str(paths)
            self.cv_out.setPlainText(msg)
            self._status("CV built")
        except Exception as exc:  # noqa: BLE001
            self.cv_out.setPlainText(f"Error: {exc}")

    # ----- Apply -----
    def _build_apply_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Apply package")
        title.setObjectName("h1")
        lay.addWidget(title)
        card = _card()
        fl = QFormLayout(card)
        fl.setContentsMargins(20, 20, 20, 20)
        self.apply_job_id = QLineEdit()
        self.apply_job_id.setPlaceholderText("job id from board")
        fl.addRow("Job ID", self.apply_job_id)
        lay.addWidget(card)
        row = QHBoxLayout()
        b1 = QPushButton("Use selected job")
        b1.clicked.connect(self._fill_selected_job)
        b2 = QPushButton("Prepare package")
        b2.setStyleSheet(
            "QPushButton { background: #06b6d4; color: #042f2e; border: none; border-radius: 10px; "
            "padding: 10px 18px; font-weight: 700; }"
        )
        b2.clicked.connect(self.do_apply)
        for b in (b1, b2):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            if b is b1:
                b.setStyleSheet(
                    "QPushButton { background: #1e293b; border: 1px solid #334155; border-radius: 10px; "
                    "padding: 10px 16px; }"
                )
            row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)
        self.apply_out = QTextEdit()
        self.apply_out.setReadOnly(True)
        lay.addWidget(self.apply_out, 1)
        return page

    def _fill_selected_job(self) -> None:
        rows = self.jobs_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "NeraJob", "Select a job on the Job board first.")
            return
        item = self.jobs_table.item(rows[0].row(), 0)
        if item:
            self.apply_job_id.setText(item.text())

    def do_apply(self) -> None:
        jid = self.apply_job_id.text().strip()
        if not jid:
            QMessageBox.warning(self, "NeraJob", "Enter a job id.")
            return
        job = get_job(jid)
        if not job:
            QMessageBox.warning(self, "NeraJob", f"Job not found: {jid}")
            return
        try:
            profile = load_profile() or default_profile()
            package, path = prepare_application(profile, job)
            self.apply_out.setPlainText(
                f"Package: {path}\n"
                f"Cover note preview:\n\n{package.cover_note}\n\n"
                f"Checklist:\n" + "\n".join(f"- {c}" for c in package.checklist)
            )
            self._status(f"Apply package ready for {jid}")
        except Exception as exc:  # noqa: BLE001
            self.apply_out.setPlainText(f"Error: {exc}")
