import re
import shutil
from pathlib import Path

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QDropEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QInputDialog,
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
from core.worker import RAW_ONLY, FORMATTED_ONLY, BOTH


def _is_youtube_url(url: str) -> bool:
    return "youtube.com/watch" in url or "youtu.be/" in url


class OutputTreeWidget(QTreeWidget):
    def __init__(self, panel: "InputPanel") -> None:
        super().__init__()
        self._panel = panel
        self.setHeaderHidden(True)
        self.setAnimated(True)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)

    def dropEvent(self, event: QDropEvent) -> None:
        dragged = self.currentItem()
        if not dragged:
            event.ignore()
            return

        src_path = Path(dragged.data(0, Qt.ItemDataRole.UserRole))
        target_item = self.itemAt(event.position().toPoint())

        if target_item:
            tgt_path = Path(target_item.data(0, Qt.ItemDataRole.UserRole))
            dest_dir = tgt_path if tgt_path.is_dir() else tgt_path.parent
        else:
            dest_dir = OUTPUT_DIR

        # Prevent moving a folder into its own subtree
        try:
            dest_dir.resolve().relative_to(src_path.resolve())
            event.ignore()
            return
        except ValueError:
            pass

        dest = dest_dir / src_path.name
        if dest == src_path:
            event.ignore()
            return

        if dest.exists():
            QMessageBox.warning(
                self, "Move Failed",
                f"'{src_path.name}' already exists in the destination.",
            )
            event.ignore()
            return

        try:
            shutil.move(str(src_path), str(dest))
        except OSError as exc:
            QMessageBox.warning(self, "Move Failed", str(exc))
            event.ignore()
            return

        event.accept()
        self._panel.refresh_output_tree()

    def _on_context_menu(self, pos: QPoint) -> None:
        item = self.itemAt(pos)
        if not item:
            return
        path = Path(item.data(0, Qt.ItemDataRole.UserRole))
        menu = QMenu(self)
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        format_action = None
        if path.is_file() and path.suffix == ".md":
            menu.addSeparator()
            format_action = menu.addAction("Format with doc-formatter")
        action = menu.exec(self.viewport().mapToGlobal(pos))
        if action == rename_action:
            self._rename_item(path)
        elif action == delete_action:
            self._delete_item(path)
        elif action is not None and action == format_action:
            self._panel.format_file_requested.emit(str(path))

    def _rename_item(self, path: Path) -> None:
        new_name, ok = QInputDialog.getText(
            self, "Rename", "New name:", text=path.name
        )
        if not ok:
            return
        new_name = re.sub(r'[<>:"/\\|?*]', "-", new_name.strip()).strip()
        if not new_name or new_name == path.name:
            return
        dest = path.parent / new_name
        if dest.exists():
            QMessageBox.warning(self, "Rename Failed", f"'{new_name}' already exists.")
            return
        try:
            path.rename(dest)
            self._panel.refresh_output_tree()
        except OSError as exc:
            QMessageBox.critical(self, "Rename Failed", str(exc))

    def _delete_item(self, path: Path) -> None:
        kind = "folder" if path.is_dir() else "file"
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete {kind} '{path.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            self._panel.refresh_output_tree()
        except OSError as exc:
            QMessageBox.critical(self, "Delete Failed", str(exc))


class InputPanel(QWidget):
    open_file_requested = pyqtSignal(str)
    format_file_requested = pyqtSignal(str)  # path to an existing .md file

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
        raw = self._subfolder_input.text().strip()
        return raw.replace("\\", "/").strip("/")

    @property
    def output_mode(self) -> str:
        return self._output_mode_combo.currentData()

    def set_processing(self, active: bool) -> None:
        self._url_input.setEnabled(not active)
        self._add_btn.setEnabled(not active)
        self._output_mode_combo.setEnabled(not active)
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
        self._clear_btn.setObjectName("secondaryBtn")
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
        subfolder_hint = QLabel("Optional — nested path inside output/")
        subfolder_hint.setStyleSheet("color: grey; font-size: 11px;")
        subfolder_hint.setWordWrap(True)
        self._subfolder_input = QLineEdit()
        self._subfolder_input.setPlaceholderText("e.g. AI/videos")

        layout.addWidget(subfolder_label)
        layout.addWidget(subfolder_hint)
        layout.addWidget(self._subfolder_input)
        layout.addWidget(_divider())

        mode_label = QLabel("Output Mode")
        mode_label.setStyleSheet("font-weight: bold;")
        self._output_mode_combo = QComboBox()
        self._output_mode_combo.addItem("Raw only (Stage 1)", RAW_ONLY)
        self._output_mode_combo.addItem("Formatted only (Stage 2)", FORMATTED_ONLY)
        self._output_mode_combo.addItem("Both (Stage 1 + Stage 2)", BOTH)
        self._output_mode_combo.setToolTip(
            "Raw only  — save to output/.../raw/\n"
            "Formatted — run doc-formatter, save to output/.../formatted/\n"
            "Both      — save raw, then also save a formatted copy"
        )

        layout.addWidget(mode_label)
        layout.addWidget(self._output_mode_combo)

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

        btn_row = QHBoxLayout()
        self._new_folder_btn = QPushButton("New Folder")
        self._new_folder_btn.setObjectName("secondaryBtn")
        btn_row.addWidget(self._new_folder_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

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
        self._new_folder_btn.clicked.connect(self._on_new_folder)

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

    def _on_new_folder(self) -> None:
        parent = self._selected_output_folder()
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if not ok or not name.strip():
            return
        name = re.sub(r'[<>:"/\\|?*]', "-", name.strip()).strip()
        if not name:
            return
        target = (parent if parent else OUTPUT_DIR) / name
        try:
            target.mkdir(parents=False, exist_ok=False)
            self.refresh_output_tree()
        except OSError as exc:
            QMessageBox.warning(self, "Create Failed", str(exc))

    def _selected_output_folder(self) -> Path | None:
        item = self._output_tree.currentItem()
        if not item:
            return None
        path = Path(item.data(0, Qt.ItemDataRole.UserRole))
        return path if path.is_dir() else path.parent

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
            self._queue_count_label.setText(
                f"{count} source{'s' if count > 1 else ''} queued"
            )
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
