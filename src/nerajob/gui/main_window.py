"""NeraJob modern desktop shell (PySide6) — polished layout."""

from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QSplitter,
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


def _primary_btn(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("primaryBtn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def _secondary_btn(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("secondaryBtn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def _ghost_btn(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("ghostBtn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def _page_header(title: str, subtitle: str, actions: list[QWidget] | None = None) -> QWidget:
    wrap = QWidget()
    row = QHBoxLayout(wrap)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(16)
    col = QVBoxLayout()
    col.setSpacing(4)
    t = QLabel(title)
    t.setObjectName("h1")
    s = QLabel(subtitle)
    s.setObjectName("h2")
    s.setWordWrap(True)
    col.addWidget(t)
    col.addWidget(s)
    row.addLayout(col, 1)
    if actions:
        act = QHBoxLayout()
        act.setSpacing(8)
        for w in actions:
            act.addWidget(w)
        row.addLayout(act)
    return wrap


def _stat_card(value: str, label: str) -> QFrame:
    f = QFrame()
    f.setObjectName("statCard")
    lay = QVBoxLayout(f)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(2)
    v = QLabel(value)
    v.setObjectName("statValue")
    v.setAlignment(Qt.AlignmentFlag.AlignLeft)
    lbl = QLabel(label)
    lbl.setObjectName("statLabel")
    lay.addWidget(v)
    lay.addWidget(lbl)
    f.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    # keep refs for updates
    f._value_label = v  # type: ignore[attr-defined]
    return f


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"NeraJob · v{__version__}")
        self.resize(1280, 800)
        self.setMinimumSize(QSize(1024, 640))
        self.setStyleSheet(STYLESHEET)

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_main(), 1)

        sb = QStatusBar()
        self.setStatusBar(sb)
        self._status("Ready · sample source works offline")
        self._goto("scan")
        self.refresh_jobs_table()
        self._refresh_stats()

    # ----- shell -----
    def _build_sidebar(self) -> QFrame:
        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(232)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(14, 18, 14, 14)
        sl.setSpacing(4)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(8)
        mark = QLabel("NJ")
        mark.setObjectName("brandMark")
        brand = QLabel("NeraJob")
        brand.setObjectName("brand")
        brand_row.addWidget(mark)
        brand_row.addWidget(brand)
        brand_row.addStretch(1)
        sl.addLayout(brand_row)
        sub = QLabel("Scan · CV · Apply · local-first")
        sub.setObjectName("brandSub")
        sl.addWidget(sub)
        sl.addSpacing(10)

        sec = QLabel("WORKSPACE")
        sec.setObjectName("navSection")
        sl.addWidget(sec)

        self._nav_btns: list[QPushButton] = []
        # ASCII labels only — emoji often render as □ in grab()/README previews
        self._nav_meta = [
            ("scan", "Scan jobs"),
            ("jobs", "Job board"),
            ("profile", "Profile"),
            ("cv", "Build CV"),
            ("apply", "Apply pack"),
        ]
        for key, label in self._nav_meta:
            b = QPushButton(label)
            b.setObjectName("navBtn")
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _=False, k=key: self._goto(k))
            self._nav_btns.append(b)
            sl.addWidget(b)

        sl.addStretch(1)
        chip = QLabel(f"v{__version__}")
        chip.setObjectName("chip")
        chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sl.addWidget(chip)
        return side

    def _build_main(self) -> QWidget:
        main = QWidget()
        main.setObjectName("content")
        lay = QVBoxLayout(main)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # top bar with live stats
        top = QFrame()
        top.setObjectName("topbar")
        top.setFixedHeight(64)
        tl = QHBoxLayout(top)
        tl.setContentsMargins(24, 10, 24, 10)
        tl.setSpacing(12)
        self.top_title = QLabel("Scan jobs")
        self.top_title.setObjectName("h1")
        font = QFont(self.top_title.font())
        font.setPointSize(15)
        font.setBold(True)
        self.top_title.setFont(font)
        tl.addWidget(self.top_title)
        tl.addStretch(1)
        self.stat_jobs = _stat_card("0", "Jobs cached")
        self.stat_sources = _stat_card(str(len(available_scrapers())), "Sources")
        for s in (self.stat_jobs, self.stat_sources):
            s.setFixedWidth(120)
            s.setFixedHeight(48)
            # compact stats in topbar
            s.layout().setContentsMargins(12, 6, 12, 6)
            s._value_label.setStyleSheet(
                'font-family: "Segoe UI", Arial, sans-serif; font-size: 16px; font-weight: 700; color: #f8fafc;'
            )  # type: ignore[attr-defined]
            tl.addWidget(s)
        lay.addWidget(top)

        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)

        self.pages = {
            "scan": self._build_scan_page(),
            "jobs": self._build_jobs_page(),
            "profile": self._build_profile_page(),
            "cv": self._build_cv_page(),
            "apply": self._build_apply_page(),
        }
        self._page_keys = list(self.pages.keys())
        self._page_titles = {
            "scan": "Scan jobs",
            "jobs": "Job board",
            "profile": "Profile",
            "cv": "Build CV",
            "apply": "Apply pack",
        }
        for w in self.pages.values():
            self.stack.addWidget(w)
        return main

    def _status(self, msg: str) -> None:
        self.statusBar().showMessage(msg)

    def _goto(self, key: str) -> None:
        idx = self._page_keys.index(key)
        self.stack.setCurrentIndex(idx)
        for i, b in enumerate(self._nav_btns):
            b.setChecked(i == idx)
        self.top_title.setText(self._page_titles.get(key, key))
        if key == "jobs":
            self.refresh_jobs_table()

    def _refresh_stats(self) -> None:
        n = len(load_jobs())
        self.stat_jobs._value_label.setText(str(n))  # type: ignore[attr-defined]
        self.stat_sources._value_label.setText(str(len(available_scrapers())))  # type: ignore[attr-defined]

    # ----- Scan -----
    def _build_scan_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(28, 20, 28, 24)
        outer.setSpacing(16)

        btn_run = _primary_btn("Run scan")
        btn_run.clicked.connect(self.do_scan)
        btn_all = _secondary_btn("Scan all sources")
        btn_all.clicked.connect(self.do_scan_all)
        outer.addWidget(
            _page_header(
                "Scan job sources",
                "Pull listings into your local jobs cache. Sample works fully offline.",
                [btn_all, btn_run],
            )
        )

        # form card — 2×2 grid for airy layout
        card = _card()
        grid = QGridLayout(card)
        grid.setContentsMargins(22, 20, 22, 20)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(14)

        def field_label(text: str) -> QLabel:
            lb = QLabel(text)
            lb.setObjectName("statLabel")
            return lb

        self.scan_query = QLineEdit()
        self.scan_query.setPlaceholderText("e.g. python backend, react, devops")
        self.scan_query.setText("python")
        self.scan_loc = QLineEdit()
        self.scan_loc.setPlaceholderText("remote / city / region")
        self.scan_loc.setText("remote")
        self.scan_source = QComboBox()
        self.scan_source.addItems(sorted(available_scrapers().keys()))
        if self.scan_source.findText("sample") >= 0:
            self.scan_source.setCurrentText("sample")
        self.scan_limit = QSpinBox()
        self.scan_limit.setRange(1, 100)
        self.scan_limit.setValue(20)

        grid.addWidget(field_label("KEYWORDS"), 0, 0)
        grid.addWidget(field_label("LOCATION"), 0, 1)
        grid.addWidget(self.scan_query, 1, 0)
        grid.addWidget(self.scan_loc, 1, 1)
        grid.addWidget(field_label("SOURCE"), 2, 0)
        grid.addWidget(field_label("LIMIT"), 2, 1)
        grid.addWidget(self.scan_source, 3, 0)
        grid.addWidget(self.scan_limit, 3, 1)
        outer.addWidget(card)

        log_label = QLabel("Activity")
        log_label.setObjectName("statLabel")
        outer.addWidget(log_label)
        self.scan_log = QTextEdit()
        self.scan_log.setReadOnly(True)
        self.scan_log.setPlaceholderText("Scan output appears here…")
        self.scan_log.setMinimumHeight(200)
        outer.addWidget(self.scan_log, 1)
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
                lines.append(f"  ✓ {name}: {len(found)} hits")
                collected.extend(found)
            except Exception as exc:  # noqa: BLE001
                lines.append(f"  ✗ {name}: {exc}")
        if not collected and "sample" not in names:
            found = get_scraper("sample").search(query=q, location=loc, limit=limit)
            lines.append(f"  ✓ fallback sample: {len(found)} hits")
            collected.extend(found)
        merged = upsert_jobs(collected)
        lines.append(f"Saved. Total jobs in cache: {len(merged)}")
        self.scan_log.setPlainText("\n".join(lines))
        self.refresh_jobs_table()
        self._refresh_stats()
        self._status(f"Scan done · {len(collected)} fetched · {len(merged)} total cached")

    # ----- Jobs -----
    def _build_jobs_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(28, 20, 28, 24)
        outer.setSpacing(14)

        btn_ref = _secondary_btn("Refresh")
        btn_ref.clicked.connect(self.refresh_jobs_table)
        btn_use = _primary_btn("Use in Apply")
        btn_use.clicked.connect(self._use_selected_for_apply)
        outer.addWidget(
            _page_header(
                "Job board",
                "Local cache (data/jobs.json). Select a row to inspect details or prepare apply.",
                [btn_ref, btn_use],
            )
        )

        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)

        # table side
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        self.jobs_table = QTableWidget(0, 5)
        self.jobs_table.setHorizontalHeaderLabels(
            ["ID", "Source", "Title", "Company", "Location"]
        )
        hdr = self.jobs_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.jobs_table.verticalHeader().setVisible(False)
        self.jobs_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.jobs_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.jobs_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.jobs_table.setShowGrid(False)
        self.jobs_table.setAlternatingRowColors(False)
        self.jobs_table.setWordWrap(False)
        self.jobs_table.itemSelectionChanged.connect(self._on_job_selected)
        ll.addWidget(self.jobs_table)
        split.addWidget(left)

        # detail side
        detail = QFrame()
        detail.setObjectName("detailPanel")
        detail.setMinimumWidth(280)
        detail.setMaximumWidth(400)
        dl = QVBoxLayout(detail)
        dl.setContentsMargins(18, 16, 18, 16)
        dl.setSpacing(10)
        dt = QLabel("Job detail")
        dt.setObjectName("h1")
        font = QFont(dt.font())
        font.setPointSize(13)
        font.setBold(True)
        dt.setFont(font)
        dl.addWidget(dt)
        self.job_detail = QTextEdit()
        self.job_detail.setReadOnly(True)
        self.job_detail.setPlaceholderText("Select a job to preview title, company, tags…")
        dl.addWidget(self.job_detail, 1)
        split.addWidget(detail)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)
        split.setSizes([720, 320])

        outer.addWidget(split, 1)
        return page

    def _on_job_selected(self) -> None:
        rows = self.jobs_table.selectionModel().selectedRows()
        if not rows:
            return
        jid = self.jobs_table.item(rows[0].row(), 0)
        if not jid:
            return
        job = get_job(jid.text())
        if not job:
            self.job_detail.setPlainText("Job not found in cache.")
            return
        tags = ", ".join(job.tags) if getattr(job, "tags", None) else "—"
        remote = "yes" if getattr(job, "remote", False) else "no"
        desc = (getattr(job, "description", None) or "")[:800]
        self.job_detail.setPlainText(
            f"{job.title}\n"
            f"{job.company}  ·  {job.location}\n"
            f"source: {job.source}  ·  remote: {remote}\n"
            f"id: {job.id}\n"
            f"url: {getattr(job, 'url', '') or '—'}\n"
            f"tags: {tags}\n\n"
            f"{desc}"
        )

    def _use_selected_for_apply(self) -> None:
        self._fill_selected_job()
        if self.apply_job_id.text().strip():
            self._goto("apply")

    def refresh_jobs_table(self) -> None:
        jobs = load_jobs()
        self.jobs_table.setRowCount(len(jobs))
        for r, job in enumerate(jobs):
            vals = [job.id, job.source, job.title, job.company, job.location]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                if c == 0:
                    item.setToolTip(str(val))
                self.jobs_table.setItem(r, c, item)
        self._refresh_stats()

    # ----- Profile -----
    def _build_profile_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(28, 20, 28, 24)
        outer.setSpacing(16)

        b1 = _secondary_btn("Reload")
        b1.clicked.connect(self.load_profile_ui)
        b2 = _primary_btn("Save profile")
        b2.clicked.connect(self.save_profile_ui)
        outer.addWidget(
            _page_header(
                "Profile",
                "Stored in data/profile.json — used for CV and apply packages.",
                [b1, b2],
            )
        )

        grid = QHBoxLayout()
        grid.setSpacing(16)

        left = _card()
        fl = QFormLayout(left)
        fl.setContentsMargins(20, 18, 20, 18)
        fl.setSpacing(12)
        fl.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.prof_name = QLineEdit()
        self.prof_title = QLineEdit()
        self.prof_email = QLineEdit()
        self.prof_skills = QLineEdit()
        self.prof_skills.setPlaceholderText("python, fastapi, postgres")
        fl.addRow("Full name", self.prof_name)
        fl.addRow("Headline", self.prof_title)
        fl.addRow("Email", self.prof_email)
        fl.addRow("Skills", self.prof_skills)
        grid.addWidget(left, 1)

        right = _card()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(20, 18, 20, 18)
        rl.setSpacing(8)
        lab = QLabel("SUMMARY")
        lab.setObjectName("statLabel")
        rl.addWidget(lab)
        self.prof_summary = QTextEdit()
        self.prof_summary.setPlaceholderText("Short professional summary…")
        self.prof_summary.setMinimumHeight(160)
        rl.addWidget(self.prof_summary, 1)
        grid.addWidget(right, 1)

        outer.addLayout(grid)
        outer.addStretch(1)
        self.load_profile_ui()
        return page

    def load_profile_ui(self) -> None:
        p = load_profile()
        if not p:
            p = default_profile()
            save_profile(p)
        data = p.model_dump() if hasattr(p, "model_dump") else {}
        self.prof_name.setText(str(data.get("full_name") or data.get("name") or ""))
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
        outer = QVBoxLayout(page)
        outer.setContentsMargins(28, 20, 28, 24)
        outer.setSpacing(16)

        btn = _primary_btn("Generate CV files")
        btn.clicked.connect(self.do_cv)
        outer.addWidget(
            _page_header(
                "Build CV",
                "Generate tailored CV artifacts from your profile for a target role.",
                [btn],
            )
        )

        card = _card()
        fl = QFormLayout(card)
        fl.setContentsMargins(20, 18, 20, 18)
        fl.setSpacing(12)
        self.cv_target = QLineEdit("Backend Engineer")
        fl.addRow("Target role", self.cv_target)
        outer.addWidget(card)

        lab = QLabel("OUTPUT")
        lab.setObjectName("statLabel")
        outer.addWidget(lab)
        self.cv_out = QTextEdit()
        self.cv_out.setReadOnly(True)
        self.cv_out.setPlaceholderText("Generated file paths appear here…")
        outer.addWidget(self.cv_out, 1)
        return page

    def do_cv(self) -> None:
        try:
            profile = load_profile() or default_profile()
            paths = write_cv_files(profile, target_role=self.cv_target.text().strip() or "Engineer")
            msg = (
                "\n".join(f"{k}: {v}" for k, v in paths.items())
                if isinstance(paths, dict)
                else str(paths)
            )
            self.cv_out.setPlainText(msg)
            self._status("CV built")
        except Exception as exc:  # noqa: BLE001
            self.cv_out.setPlainText(f"Error: {exc}")

    # ----- Apply -----
    def _build_apply_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(28, 20, 28, 24)
        outer.setSpacing(16)

        b1 = _secondary_btn("Use selected job")
        b1.clicked.connect(self._fill_selected_job)
        b2 = _primary_btn("Prepare package")
        b2.clicked.connect(self.do_apply)
        outer.addWidget(
            _page_header(
                "Apply package",
                "Build a cover note + checklist for a cached job id.",
                [b1, b2],
            )
        )

        card = _card()
        fl = QFormLayout(card)
        fl.setContentsMargins(20, 18, 20, 18)
        fl.setSpacing(12)
        self.apply_job_id = QLineEdit()
        self.apply_job_id.setPlaceholderText("job id from board (or Use selected job)")
        fl.addRow("Job ID", self.apply_job_id)
        outer.addWidget(card)

        lab = QLabel("PACKAGE PREVIEW")
        lab.setObjectName("statLabel")
        outer.addWidget(lab)
        self.apply_out = QTextEdit()
        self.apply_out.setReadOnly(True)
        self.apply_out.setPlaceholderText("Cover note and checklist preview…")
        outer.addWidget(self.apply_out, 1)
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
                f"Package: {path}\n\n"
                f"Cover note preview:\n{package.cover_note}\n\n"
                f"Checklist:\n" + "\n".join(f"• {c}" for c in package.checklist)
            )
            self._status(f"Apply package ready for {jid}")
        except Exception as exc:  # noqa: BLE001
            self.apply_out.setPlainText(f"Error: {exc}")
