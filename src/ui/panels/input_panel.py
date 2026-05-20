from pathlib import Path

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QStyle,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.paths import OUTPUT_DIR


def _is_youtube_url(url: str) -> bool:
    return "youtube.com/watch" in url or "youtu.be/" in url


class OutputTreeWidget(QTreeWidget):
    def __init__(self, panel: "InputPanel") -> None:
        super().__init__()
        self._panel = panel
        self.setHeaderHidden(True)
        self.setAnimated(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)

    def _on_context_menu(self, pos: QPoint) -> None:
        item = self.itemAt(pos)
        if not item:
            return
        path = Path(item.data(0, Qt.ItemDataRole.UserRole))
        if not path.is_file():
            return
        menu = QMenu(self)
        delete_action = menu.addAction("Delete")
        action = menu.exec(self.viewport().mapToGlobal(pos))
        if action == delete_action:
            self._delete_item(path)

    def _delete_item(self, path: Path) -> None:
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete '{path.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            path.unlink()
            self._panel.refresh_output_tree()
        except OSError as exc:
            QMessageBox.critical(self, "Delete Failed", str(exc))


class InputPanel(QWidget):
    open_file_requested = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(240)
        self.setMaximumWidth(400)
        self._queued_sources: list[str] = []
        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def take_sources(self) -> list[str]:
        sources = list(self._queued_sources)
        self._queued_sources.clear()
        self._refresh_queue_list()
        return sources

    @property
    def subfolder(self) -> str:
        return self._subfolder_input.text().strip()

    def set_processing(self, active: bool) -> None:
        self._url_input.setEnabled(not active)
        self._add_btn.setEnabled(not active)
        self.convert_btn.setEnabled(not active)

    def refresh_output_tree(self) -> None:
        self._output_tree.clear()
        if OUTPUT_DIR.exists():
            _populate_tree(self._output_tree.invisibleRootItem(), OUTPUT_DIR, self)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_add_tab(), "Add Sources")
        self._tabs.addTab(self._build_output_tab(), "Output Files")
        layout.addWidget(self._tabs)

    def _build_add_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(10)

        url_label = QLabel("URL")
        url_label.setStyleSheet("font-weight: bold;")
        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("YouTube or web article URL")
        self._add_btn = QPushButton("Add to Queue")
        self._add_btn.setEnabled(False)

        layout.addWidget(url_label)
        layout.addWidget(self._url_input)
        layout.addWidget(self._add_btn)
        layout.addWidget(_divider())

        queue_label = QLabel("Queue")
        queue_label.setStyleSheet("font-weight: bold;")
        self._queue_list = QListWidget()
        self._queue_list.setMaximumHeight(140)
        self._queue_list.setWordWrap(True)

        clear_row = QHBoxLayout()
        self._queue_count_label = QLabel("No sources queued")
        self._queue_count_label.setStyleSheet("color: grey; font-size: 11px;")
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setEnabled(False)
        self._clear_btn.setMaximumWidth(60)
        clear_row.addWidget(self._queue_count_label)
        clear_row.addStretch()
        clear_row.addWidget(self._clear_btn)

        layout.addWidget(queue_label)
        layout.addLayout(clear_row)
        layout.addWidget(self._queue_list)
        layout.addWidget(_divider())

        subfolder_label = QLabel("Output Subfolder")
        subfolder_label.setStyleSheet("font-weight: bold;")
        subfolder_hint = QLabel("Optional — creates nested folders inside output/")
        subfolder_hint.setStyleSheet("color: grey; font-size: 11px;")
        subfolder_hint.setWordWrap(True)
        self._subfolder_input = QLineEdit()
        self._subfolder_input.setPlaceholderText("e.g. AI/videos")

        layout.addWidget(subfolder_label)
        layout.addWidget(subfolder_hint)
        layout.addWidget(self._subfolder_input)
        layout.addWidget(_divider())

        self.convert_btn = QPushButton("Convert")
        self.convert_btn.setEnabled(False)
        layout.addWidget(self.convert_btn)
        layout.addStretch()
        return widget

    def _build_output_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(8)

        self._output_tree = OutputTreeWidget(self)
        layout.addWidget(self._output_tree)

        self.refresh_output_tree()
        return widget

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._url_input.textChanged.connect(self._on_url_changed)
        self._url_input.returnPressed.connect(self._on_add_url)
        self._add_btn.clicked.connect(self._on_add_url)
        self._clear_btn.clicked.connect(self._on_clear_queue)
        self._output_tree.itemDoubleClicked.connect(self._on_output_item_double_click)

    def _on_url_changed(self, text: str) -> None:
        self._add_btn.setEnabled(bool(text.strip()))

    def _on_add_url(self) -> None:
        url = self._url_input.text().strip()
        if not url:
            return
        self._queued_sources.append(url)
        self._url_input.clear()
        self._refresh_queue_list()

    def _on_clear_queue(self) -> None:
        self._queued_sources.clear()
        self._refresh_queue_list()

    def _on_output_item_double_click(self, item: QTreeWidgetItem, _col: int) -> None:
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and Path(path).is_file():
            self.open_file_requested.emit(path)

    def _refresh_queue_list(self) -> None:
        self._queue_list.clear()
        for source in self._queued_sources:
            badge = "[YT]" if _is_youtube_url(source) else "[Web]"
            item = QListWidgetItem(f"{badge} {source}")
            self._queue_list.addItem(item)
        count = len(self._queued_sources)
        if count == 0:
            self._queue_count_label.setText("No sources queued")
        else:
            self._queue_count_label.setText(f"{count} source{'s' if count > 1 else ''} queued")
        self.convert_btn.setEnabled(count > 0)
        self._clear_btn.setEnabled(count > 0)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _populate_tree(parent_item: QTreeWidgetItem, folder: Path, panel: InputPanel) -> None:
    dirs = sorted(p for p in folder.iterdir() if p.is_dir())
    files = sorted(
        p for p in folder.iterdir() if p.is_file() and p.name != ".gitkeep"
    )

    style = panel.style()
    dir_icon = style.standardIcon(QStyle.StandardPixmap.SP_DirIcon)
    file_icon = style.standardIcon(QStyle.StandardPixmap.SP_FileIcon)

    for d in dirs:
        item = QTreeWidgetItem([d.name])
        item.setIcon(0, dir_icon)
        item.setData(0, Qt.ItemDataRole.UserRole, str(d))
        _populate_tree(item, d, panel)
        parent_item.addChild(item)

    for f in files:
        item = QTreeWidgetItem([f.name])
        item.setIcon(0, file_icon)
        item.setData(0, Qt.ItemDataRole.UserRole, str(f))
        parent_item.addChild(item)


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
