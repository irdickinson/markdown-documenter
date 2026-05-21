import re
import shutil
from pathlib import Path

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QDropEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
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
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.ai_formatter import DEFAULT_MODEL
from core.paths import OUTPUT_DIR
from core.worker import RAW_ONLY, FORMATTED_ONLY, BOTH


def _is_youtube_url(url: str) -> bool:
    return "youtube.com/watch" in url or "youtu.be/" in url


def _section_label(text: str) -> QLabel:
    label = QLabel(text.upper())
    label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 700;")
    return label


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
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
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
    format_file_requested = pyqtSignal(str)       # single file (right-click)
    format_files_requested = pyqtSignal(list)     # multiple files (Format Selected button)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(260)
        self.setMaximumWidth(380)
        self._queued_sources: list[str] = []
        self._build_ui()
        self._connect_signals()
        self._refresh_formatter_models()

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

    @property
    def formatting_mode(self) -> str:
        return self._format_depth_combo.currentData()

    @property
    def formatting_model(self) -> str:
        return self._model_combo.currentText().strip() or DEFAULT_MODEL

    def set_processing(self, active: bool) -> None:
        self._url_input.setEnabled(not active)
        self._add_btn.setEnabled(not active and bool(self._url_input.text().strip()))
        self._output_mode_combo.setEnabled(not active)
        self._format_depth_combo.setEnabled(not active)
        self._model_combo.setEnabled(not active)
        self._model_refresh_btn.setEnabled(not active)
        self._subfolder_input.setEnabled(not active)
        self._format_selected_btn.setEnabled(not active and self._has_selected_md_files())
        self.stop_btn.setEnabled(active)
        if not active:
            self.convert_btn.setEnabled(bool(self._queued_sources))

    def refresh_output_tree(self) -> None:
        self._output_tree.clear()
        if OUTPUT_DIR.exists():
            _populate_tree(self._output_tree.invisibleRootItem(), OUTPUT_DIR, self)
        self._update_format_selected_btn()

    def refresh_formatter_models(self) -> None:
        self._refresh_formatter_models()

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
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setSpacing(0)

        # --- URL ---
        layout.addWidget(_section_label("Source URL"))
        layout.addSpacing(5)
        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("YouTube or article URL")
        layout.addWidget(self._url_input)
        layout.addSpacing(6)
        self._add_btn = QPushButton("Add to Queue")
        self._add_btn.setEnabled(False)
        layout.addWidget(self._add_btn)
        layout.addSpacing(18)

        # --- Queue ---
        queue_header = QHBoxLayout()
        self._queue_count_label = QLabel("QUEUE")
        self._queue_count_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 700;")
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setObjectName("secondaryBtn")
        self._clear_btn.setEnabled(False)
        self._clear_btn.setMaximumWidth(52)
        self._clear_btn.setMinimumHeight(20)
        queue_header.addWidget(self._queue_count_label)
        queue_header.addStretch()
        queue_header.addWidget(self._clear_btn)
        layout.addLayout(queue_header)
        layout.addSpacing(5)
        self._queue_list = QListWidget()
        self._queue_list.setMaximumHeight(100)
        self._queue_list.setWordWrap(True)
        layout.addWidget(self._queue_list)
        layout.addSpacing(18)

        # --- Output subfolder ---
        layout.addWidget(_section_label("Output Subfolder  (optional)"))
        layout.addSpacing(5)
        self._subfolder_input = QLineEdit()
        self._subfolder_input.setPlaceholderText("e.g. AI/videos  →  output/AI/videos/")
        layout.addWidget(self._subfolder_input)
        layout.addSpacing(18)

        # --- Output mode ---
        layout.addWidget(_section_label("Output"))
        layout.addSpacing(5)
        self._output_mode_combo = QComboBox()
        self._output_mode_combo.addItem("Raw only (Stage 1)", RAW_ONLY)
        self._output_mode_combo.addItem("Formatted only (Stage 2)", FORMATTED_ONLY)
        self._output_mode_combo.addItem("Both  —  raw + formatted", BOTH)
        self._output_mode_combo.setToolTip(
            "Raw only  →  output/.../raw/\n"
            "Formatted  →  doc-formatter pass, output/.../formatted/\n"
            "Both  →  saves raw then also a formatted copy"
        )
        layout.addWidget(self._output_mode_combo)
        layout.addSpacing(14)

        # --- Formatting depth ---
        layout.addWidget(_section_label("Formatting Depth"))
        layout.addSpacing(5)
        self._format_depth_combo = QComboBox()
        self._format_depth_combo.addItem("Structured  (default)", "structured")
        self._format_depth_combo.addItem("Quick  —  headers only, fast", "quick")
        self._format_depth_combo.addItem("By Topic  —  reorganise by theme", "topic")
        self._format_depth_combo.setToolTip(
            "Structured: full cleanup per doc-formatter system prompt\n"
            "Quick: section headers and run-on fixes only, faster\n"
            "By Topic: groups related content into themed sections"
        )
        layout.addWidget(self._format_depth_combo)
        layout.addSpacing(14)

        # --- Formatting model ---
        layout.addWidget(_section_label("Formatting Model"))
        layout.addSpacing(5)
        model_row = QHBoxLayout()
        model_row.setSpacing(6)
        self._model_combo = QComboBox()
        self._model_combo.setToolTip("Ollama model to use for Stage 2 formatting")
        self._model_refresh_btn = QToolButton()
        self._model_refresh_btn.setText("↻")
        self._model_refresh_btn.setToolTip("Refresh model list from Ollama")
        model_row.addWidget(self._model_combo, stretch=1)
        model_row.addWidget(self._model_refresh_btn)
        layout.addLayout(model_row)
        layout.addSpacing(20)

        # --- Action buttons ---
        action_row = QHBoxLayout()
        action_row.setSpacing(6)
        self.convert_btn = QPushButton("Convert")
        self.convert_btn.setEnabled(False)
        self.convert_btn.setMinimumHeight(34)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMaximumWidth(64)
        self.stop_btn.setMinimumHeight(34)
        action_row.addWidget(self.convert_btn, stretch=1)
        action_row.addWidget(self.stop_btn)
        layout.addLayout(action_row)

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
        layout.addWidget(self._output_tree, stretch=1)

        # --- Format selected bar ---
        self._sel_label = QLabel("Select .md files to format with current settings")
        self._sel_label.setStyleSheet("color: #94a3b8; font-size: 10px;")
        self._sel_label.setWordWrap(True)
        layout.addWidget(self._sel_label)

        self._format_selected_btn = QPushButton("Format Selected Files")
        self._format_selected_btn.setEnabled(False)
        self._format_selected_btn.setMinimumHeight(30)
        layout.addWidget(self._format_selected_btn)

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
        self._output_tree.itemSelectionChanged.connect(self._update_format_selected_btn)
        self._new_folder_btn.clicked.connect(self._on_new_folder)
        self._model_refresh_btn.clicked.connect(self._refresh_formatter_models)
        self._format_selected_btn.clicked.connect(self._on_format_selected)

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

    def _on_format_selected(self) -> None:
        paths = self._selected_md_paths()
        if paths:
            self.format_files_requested.emit(paths)

    def _update_format_selected_btn(self) -> None:
        paths = self._selected_md_paths()
        n = len(paths)
        if n == 0:
            self._sel_label.setText("Select .md files to format with current settings")
            self._format_selected_btn.setText("Format Selected Files")
            self._format_selected_btn.setEnabled(False)
        else:
            self._sel_label.setText(
                f"{n} file{'s' if n > 1 else ''} selected  —  "
                "uses formatting depth and model from Add Sources"
            )
            self._format_selected_btn.setText(
                f"Format {n} File{'s' if n > 1 else ''}"
            )
            self._format_selected_btn.setEnabled(True)

    def _selected_output_folder(self) -> Path | None:
        item = self._output_tree.currentItem()
        if not item:
            return None
        path = Path(item.data(0, Qt.ItemDataRole.UserRole))
        return path if path.is_dir() else path.parent

    def _selected_md_paths(self) -> list[str]:
        return [
            item.data(0, Qt.ItemDataRole.UserRole)
            for item in self._output_tree.selectedItems()
            if Path(item.data(0, Qt.ItemDataRole.UserRole)).is_file()
            and item.data(0, Qt.ItemDataRole.UserRole).endswith(".md")
        ]

    def _has_selected_md_files(self) -> bool:
        return bool(self._selected_md_paths())

    def _refresh_formatter_models(self) -> None:
        current = self._model_combo.currentText()
        self._model_combo.clear()
        try:
            import ollama
            result = ollama.list()
            for m in result.models:
                self._model_combo.addItem(m.model)
            idx = self._model_combo.findText(current)
            if idx >= 0:
                self._model_combo.setCurrentIndex(idx)
            else:
                # Try to default to doc-formatter if present
                idx = self._model_combo.findText(DEFAULT_MODEL)
                if idx >= 0:
                    self._model_combo.setCurrentIndex(idx)
        except Exception:
            self._model_combo.addItem(DEFAULT_MODEL)

    def _refresh_queue_list(self) -> None:
        self._queue_list.clear()
        for source in self._queued_sources:
            badge = "[YT]" if _is_youtube_url(source) else "[Web]"
            item = QListWidgetItem(f"{badge}  {source}")
            self._queue_list.addItem(item)
        count = len(self._queued_sources)
        label = "QUEUE" if count == 0 else f"QUEUE  —  {count} SOURCE{'S' if count > 1 else ''}"
        self._queue_count_label.setText(label)
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
