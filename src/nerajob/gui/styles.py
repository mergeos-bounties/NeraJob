"""Modern dark theme for NeraJob Qt desktop."""

STYLESHEET = """
* {
  font-family: "Segoe UI", "Inter", "SF Pro Text", sans-serif;
  font-size: 13px;
  color: #e2e8f0;
}
QMainWindow, QWidget#central {
  background: #0b1220;
}
QFrame#sidebar {
  background: #0f172a;
  border-right: 1px solid #1e293b;
}
QLabel#brand {
  font-size: 18px;
  font-weight: 700;
  color: #22d3ee;
  padding: 8px 4px;
}
QLabel#brandSub {
  color: #64748b;
  font-size: 11px;
}
QPushButton.nav {
  text-align: left;
  padding: 12px 14px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: #94a3b8;
  font-weight: 600;
}
QPushButton.nav:hover {
  background: #1e293b;
  color: #e2e8f0;
}
QPushButton.nav:checked {
  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
    stop:0 #0e7490, stop:1 #155e75);
  color: #ecfeff;
}
QFrame#card {
  background: #111827;
  border: 1px solid #1f2937;
  border-radius: 14px;
}
QLabel#h1 {
  font-size: 22px;
  font-weight: 700;
  color: #f8fafc;
}
QLabel#h2 {
  font-size: 14px;
  font-weight: 600;
  color: #94a3b8;
}
QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 10px;
  padding: 8px 12px;
  selection-background-color: #0891b2;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
  border: 1px solid #22d3ee;
}
QPushButton.primary {
  background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #06b6d4, stop:1 #0891b2);
  color: #042f2e;
  border: none;
  border-radius: 10px;
  padding: 10px 18px;
  font-weight: 700;
}
QPushButton.primary:hover {
  background: #22d3ee;
}
QPushButton.secondary {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 10px;
  padding: 10px 16px;
  color: #e2e8f0;
  font-weight: 600;
}
QPushButton.secondary:hover {
  border-color: #22d3ee;
}
QTableWidget {
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 12px;
  gridline-color: #1e293b;
  selection-background-color: #155e75;
  selection-color: #ecfeff;
}
QHeaderView::section {
  background: #111827;
  color: #94a3b8;
  padding: 8px;
  border: none;
  border-bottom: 1px solid #1e293b;
  font-weight: 600;
}
QStatusBar {
  background: #0f172a;
  color: #64748b;
  border-top: 1px solid #1e293b;
}
QScrollBar:vertical {
  background: transparent;
  width: 10px;
}
QScrollBar::handle:vertical {
  background: #334155;
  border-radius: 5px;
  min-height: 30px;
}
"""
