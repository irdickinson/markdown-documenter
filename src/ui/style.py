from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QApplication


def apply_stylesheet(app: QApplication) -> None:
    palette = app.palette()
    dark = palette.color(QPalette.ColorRole.Window).lightness() < 128
    app.setStyleSheet(_DARK_QSS if dark else _LIGHT_QSS)


_LIGHT_QSS = """
/* === Buttons (primary — blue) === */
QPushButton {
    background-color: #2563eb;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 500;
    min-height: 26px;
}
QPushButton:hover   { background-color: #1d4ed8; }
QPushButton:pressed { background-color: #1e40af; }
QPushButton:disabled { background-color: #94a3b8; color: #f1f5f9; }

QPushButton#stopBtn { background-color: #dc2626; }
QPushButton#stopBtn:hover { background-color: #b91c1c; }
QPushButton#stopBtn:disabled { background-color: #94a3b8; }

QPushButton#secondaryBtn { background-color: #64748b; }
QPushButton#secondaryBtn:hover { background-color: #475569; }
QPushButton#secondaryBtn:disabled { background-color: #94a3b8; }

/* === Tool buttons (secondary) === */
QToolButton {
    background-color: #e2e8f0;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 4px 10px;
    font-size: 12px;
    min-height: 24px;
}
QToolButton:hover   { background-color: #cbd5e1; }
QToolButton:pressed { background-color: #bfdbfe; }
QToolButton:checked { background-color: #bfdbfe; border-color: #93c5fd; color: #1e40af; }

/* === Input fields === */
QLineEdit {
    border: 1.5px solid #cbd5e1;
    border-radius: 5px;
    padding: 5px 10px;
    font-size: 12px;
    background: white;
    selection-background-color: #bfdbfe;
    min-height: 26px;
}
QLineEdit:focus    { border-color: #2563eb; }
QLineEdit:disabled { background: #f1f5f9; color: #94a3b8; }

QTextEdit {
    border: 1.5px solid #cbd5e1;
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 12px;
    background: white;
    selection-background-color: #bfdbfe;
}
QTextEdit:focus { border-color: #2563eb; }

/* === ComboBox === */
QComboBox {
    border: 1.5px solid #cbd5e1;
    border-radius: 5px;
    padding: 5px 10px;
    font-size: 12px;
    background: white;
    min-height: 26px;
}
QComboBox:focus    { border-color: #2563eb; }
QComboBox:disabled { background: #f1f5f9; color: #94a3b8; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView { border: 1px solid #cbd5e1; selection-background-color: #bfdbfe; }

/* === Tabs === */
QTabWidget::pane { border: 1px solid #e2e8f0; top: -1px; }
QTabBar::tab {
    background: #f1f5f9;
    color: #64748b;
    padding: 7px 18px;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    margin-right: 2px;
    font-size: 12px;
}
QTabBar::tab:selected        { background: white; color: #1e293b; font-weight: 600; }
QTabBar::tab:hover:!selected { background: #e2e8f0; }

/* === Lists and trees === */
QListWidget, QTreeWidget {
    border: 1px solid #e2e8f0;
    border-radius: 5px;
    font-size: 12px;
    outline: none;
}
QListWidget::item { padding: 3px 6px; }
QListWidget::item:selected, QTreeWidget::item:selected {
    background: #dbeafe;
    color: #1e293b;
}
QListWidget::item:hover:!selected, QTreeWidget::item:hover:!selected {
    background: #f8fafc;
}

/* === Text browser (markdown preview and chat) === */
QTextBrowser {
    border: 1px solid #e2e8f0;
    border-radius: 5px;
    font-size: 13px;
    background: white;
}

/* === Scroll bars === */
QScrollBar:vertical {
    background: #f1f5f9;
    width: 10px;
    border-radius: 5px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #94a3b8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #f1f5f9;
    height: 10px;
    border-radius: 5px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #cbd5e1;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #94a3b8; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* === Status bar === */
QStatusBar {
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
    font-size: 11px;
    color: #64748b;
}

/* === Splitter === */
QSplitter::handle:horizontal { background: #e2e8f0; width: 1px; }

/* === Labels === */
QLabel { font-size: 12px; }
"""


_DARK_QSS = """
/* === Buttons (primary — blue) === */
QPushButton {
    background-color: #3b82f6;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 500;
    min-height: 26px;
}
QPushButton:hover   { background-color: #2563eb; }
QPushButton:pressed { background-color: #1d4ed8; }
QPushButton:disabled { background-color: #4b5563; color: #9ca3af; }

QPushButton#stopBtn { background-color: #ef4444; }
QPushButton#stopBtn:hover { background-color: #dc2626; }
QPushButton#stopBtn:disabled { background-color: #4b5563; }

QPushButton#secondaryBtn { background-color: #374151; }
QPushButton#secondaryBtn:hover { background-color: #4b5563; }
QPushButton#secondaryBtn:disabled { background-color: #374151; color: #6b7280; }

/* === Tool buttons === */
QToolButton {
    background-color: #374151;
    color: #e5e7eb;
    border: 1px solid #4b5563;
    border-radius: 5px;
    padding: 4px 10px;
    font-size: 12px;
    min-height: 24px;
}
QToolButton:hover   { background-color: #4b5563; }
QToolButton:pressed { background-color: #1e40af; }
QToolButton:checked { background-color: #1e40af; border-color: #3b82f6; color: #bfdbfe; }

/* === Input fields === */
QLineEdit {
    border: 1.5px solid #4b5563;
    border-radius: 5px;
    padding: 5px 10px;
    font-size: 12px;
    background: #1f2937;
    color: #e5e7eb;
    selection-background-color: #1e40af;
    min-height: 26px;
}
QLineEdit:focus    { border-color: #3b82f6; }
QLineEdit:disabled { background: #374151; color: #6b7280; }

QTextEdit {
    border: 1.5px solid #4b5563;
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 12px;
    background: #1f2937;
    color: #e5e7eb;
    selection-background-color: #1e40af;
}
QTextEdit:focus { border-color: #3b82f6; }

/* === ComboBox === */
QComboBox {
    border: 1.5px solid #4b5563;
    border-radius: 5px;
    padding: 5px 10px;
    font-size: 12px;
    background: #1f2937;
    color: #e5e7eb;
    min-height: 26px;
}
QComboBox:focus    { border-color: #3b82f6; }
QComboBox:disabled { background: #374151; color: #6b7280; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    border: 1px solid #4b5563;
    background: #1f2937;
    color: #e5e7eb;
    selection-background-color: #1e40af;
}

/* === Tabs === */
QTabWidget::pane { border: 1px solid #374151; top: -1px; }
QTabBar::tab {
    background: #1f2937;
    color: #9ca3af;
    padding: 7px 18px;
    border: 1px solid #374151;
    border-bottom: none;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    margin-right: 2px;
    font-size: 12px;
}
QTabBar::tab:selected        { background: #111827; color: #f9fafb; font-weight: 600; }
QTabBar::tab:hover:!selected { background: #374151; }

/* === Lists and trees === */
QListWidget, QTreeWidget {
    border: 1px solid #374151;
    border-radius: 5px;
    font-size: 12px;
    outline: none;
    background: #1f2937;
    color: #e5e7eb;
}
QListWidget::item { padding: 3px 6px; }
QListWidget::item:selected, QTreeWidget::item:selected {
    background: #1e40af;
    color: #f9fafb;
}
QListWidget::item:hover:!selected, QTreeWidget::item:hover:!selected {
    background: #374151;
}

/* === Text browser === */
QTextBrowser {
    border: 1px solid #374151;
    border-radius: 5px;
    font-size: 13px;
    background: #111827;
    color: #e5e7eb;
}

/* === Scroll bars === */
QScrollBar:vertical {
    background: #1f2937;
    width: 10px;
    border-radius: 5px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #4b5563;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #6b7280; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #1f2937;
    height: 10px;
    border-radius: 5px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #4b5563;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #6b7280; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* === Status bar === */
QStatusBar {
    background: #111827;
    border-top: 1px solid #374151;
    font-size: 11px;
    color: #9ca3af;
}

/* === Splitter === */
QSplitter::handle:horizontal { background: #374151; width: 1px; }

/* === Labels === */
QLabel { font-size: 12px; }
"""
