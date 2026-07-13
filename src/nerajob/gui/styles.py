"""Modern dark theme for NeraJob Qt desktop — polished layout tokens."""

STYLESHEET = """
/* Use only widely installed Windows fonts — exotic stacks (Inter / system-ui)
   can render as tofu boxes (□) in Qt grabs and some GPU drivers. */
QWidget, QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox,
QTextEdit, QPlainTextEdit, QTableWidget, QHeaderView, QStatusBar, QAbstractItemView {
  font-family: "Segoe UI", "Arial", "Helvetica", sans-serif;
  font-size: 13px;
  color: #e2e8f0;
}

/* ---- Shell ---- */
QMainWindow, QWidget#central {
  background: #0a0f1a;
}
QFrame#sidebar {
  background: #0c1424;
  border-right: 1px solid #1a2438;
}
QFrame#topbar {
  background: #0c1424;
  border-bottom: 1px solid #1a2438;
}
QWidget#content {
  background: #0a0f1a;
}
QLabel#brand {
  font-size: 18px;
  font-weight: 700;
  color: #22d3ee;
  letter-spacing: 0;
  padding: 0;
}
QLabel#brandMark {
  font-size: 18px;
  font-weight: 700;
  color: #22d3ee;
  padding: 0 2px 0 0;
}
QLabel#brandSub {
  color: #64748b;
  font-size: 11px;
  padding-top: 2px;
}
QLabel#navSection {
  color: #475569;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 12px 10px 4px 10px;
}
QPushButton#navBtn {
  text-align: left;
  padding: 11px 14px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: #94a3b8;
  font-weight: 600;
  font-size: 13px;
}
QPushButton#navBtn:hover {
  background: #152033;
  color: #f1f5f9;
}
QPushButton#navBtn:checked {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop:0 #0e7490, stop:1 #155e75);
  color: #ecfeff;
  border: 1px solid #0e749066;
}

/* ---- Typography ---- */
QLabel#h1 {
  font-size: 22px;
  font-weight: 700;
  color: #f8fafc;
  letter-spacing: 0;
}
QLabel#h2 {
  font-size: 13px;
  font-weight: 500;
  color: #94a3b8;
  line-height: 1.4;
}
QLabel#muted {
  color: #64748b;
  font-size: 12px;
}
QLabel#chip {
  background: #122033;
  border: 1px solid #1e3a4f;
  border-radius: 999px;
  padding: 4px 12px;
  color: #67e8f9;
  font-size: 11px;
  font-weight: 700;
}
QLabel#statValue {
  font-size: 20px;
  font-weight: 700;
  color: #f8fafc;
}
QLabel#statLabel {
  font-size: 11px;
  color: #64748b;
  font-weight: 600;
}

/* ---- Cards / panels ---- */
QFrame#card {
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 16px;
}
QFrame#statCard {
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 14px;
}
QFrame#detailPanel {
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 16px;
}

/* ---- Inputs ---- */
QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {
  background: #0b1220;
  border: 1px solid #2a3a52;
  border-radius: 10px;
  padding: 9px 12px;
  selection-background-color: #0891b2;
  min-height: 18px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
  border: 1px solid #22d3ee;
  background: #0c1526;
}
QComboBox::drop-down {
  border: none;
  width: 28px;
}
QComboBox QAbstractItemView {
  background: #0f172a;
  border: 1px solid #334155;
  selection-background-color: #155e75;
  outline: none;
}
QFormLayout {
  spacing: 10px;
}

/* ---- Buttons ---- */
QPushButton#primaryBtn {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06b6d4, stop:1 #0891b2);
  color: #042f2e;
  border: none;
  border-radius: 10px;
  padding: 10px 18px;
  font-weight: 700;
  min-height: 18px;
}
QPushButton#primaryBtn:hover {
  background: #22d3ee;
}
QPushButton#primaryBtn:pressed {
  background: #0891b2;
}
QPushButton#secondaryBtn {
  background: #152033;
  border: 1px solid #2a3a52;
  border-radius: 10px;
  padding: 10px 16px;
  color: #e2e8f0;
  font-weight: 600;
  min-height: 18px;
}
QPushButton#secondaryBtn:hover {
  border-color: #22d3ee;
  color: #ecfeff;
}
QPushButton#ghostBtn {
  background: transparent;
  border: 1px solid #2a3a52;
  border-radius: 10px;
  padding: 8px 14px;
  color: #94a3b8;
  font-weight: 600;
}
QPushButton#ghostBtn:hover {
  color: #e2e8f0;
  border-color: #475569;
}

/* ---- Table ---- */
QTableWidget {
  background: #0b1220;
  border: 1px solid #1e293b;
  border-radius: 14px;
  gridline-color: transparent;
  selection-background-color: #155e75;
  selection-color: #ecfeff;
  outline: none;
  padding: 4px;
}
QTableWidget::item {
  padding: 8px 10px;
  border-bottom: 1px solid #152033;
}
QTableWidget::item:selected {
  background: #155e75;
}
QHeaderView::section {
  background: #0f172a;
  color: #94a3b8;
  padding: 10px 12px;
  border: none;
  border-bottom: 1px solid #1e293b;
  font-weight: 700;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
QTableCornerButton::section {
  background: #0f172a;
  border: none;
}

/* ---- Scroll / status ---- */
QStatusBar {
  background: #0c1424;
  color: #64748b;
  border-top: 1px solid #1a2438;
  padding: 2px 8px;
}
QScrollBar:vertical {
  background: transparent;
  width: 10px;
  margin: 4px 2px;
}
QScrollBar::handle:vertical {
  background: #334155;
  border-radius: 5px;
  min-height: 32px;
}
QScrollBar::handle:vertical:hover {
  background: #475569;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
  height: 0;
}
QScrollBar:horizontal {
  background: transparent;
  height: 10px;
}
QScrollBar::handle:horizontal {
  background: #334155;
  border-radius: 5px;
  min-width: 32px;
}
QToolTip {
  background: #1e293b;
  color: #f1f5f9;
  border: 1px solid #334155;
  padding: 6px 8px;
  border-radius: 6px;
}
"""
