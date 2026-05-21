import ollama
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .panels.chat_panel import ChatPanel
from .panels.input_panel import InputPanel
from .panels.output_panel import OutputPanel
from core.format_worker import FormatWorker
from core.worker import ConversionWorker

_OLLAMA_CHECK_INTERVAL_MS = 10_000


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Markdown Documenter")
        self.setMinimumSize(900, 600)
        self.resize(1200, 720)
        self._worker: ConversionWorker | None = None
        self._format_worker: FormatWorker | None = None
        self._build_ui()
        self._connect_signals()
        self._start_ollama_polling()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_converter_tab(), "Converter")
        self._tabs.addTab(self._build_chat_tab(), "Chat")
        root.addWidget(self._tabs)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        self._throbber = QProgressBar()
        self._throbber.setRange(0, 0)
        self._throbber.setMaximumWidth(120)
        self._throbber.setMaximumHeight(16)
        self._throbber.hide()
        self.status_bar.addPermanentWidget(self._throbber)

        self._ollama_label = QLabel()
        self._ollama_label.setContentsMargins(0, 0, 8, 0)
        self.status_bar.addPermanentWidget(self._ollama_label)

    def _build_converter_tab(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.input_panel = InputPanel()
        self.output_panel = OutputPanel()
        splitter.addWidget(self.input_panel)
        splitter.addWidget(self.output_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([280, 920])

        layout.addWidget(splitter)
        return widget

    def _build_chat_tab(self) -> QWidget:
        self.chat_panel = ChatPanel()
        return self.chat_panel

    def _connect_signals(self) -> None:
        self.input_panel.convert_btn.clicked.connect(self._on_convert)
        self.input_panel.open_file_requested.connect(self.output_panel.open_file)
        self.input_panel.format_file_requested.connect(self._on_format_file)

    def _start_ollama_polling(self) -> None:
        self._check_ollama_status()
        self._ollama_timer = QTimer(self)
        self._ollama_timer.setInterval(_OLLAMA_CHECK_INTERVAL_MS)
        self._ollama_timer.timeout.connect(self._check_ollama_status)
        self._ollama_timer.start()

    def _check_ollama_status(self) -> None:
        if _ollama_running():
            self._ollama_label.setText("● Ollama ready")
            self._ollama_label.setStyleSheet("color: #4caf50; font-size: 11px;")
            self.chat_panel.refresh_models()
        else:
            self._ollama_label.setText("● Ollama not running")
            self._ollama_label.setStyleSheet("color: #f44336; font-size: 11px;")

    def _on_convert(self) -> None:
        sources = self.input_panel.take_sources()
        if not sources:
            return

        self.input_panel.set_processing(True)
        self.output_panel.clear()
        self._throbber.show()
        self.status_bar.showMessage("Starting…")

        self._worker = ConversionWorker(
            sources,
            self.input_panel.subfolder,
            output_mode=self.input_panel.output_mode,
        )
        self._worker.progress.connect(self.status_bar.showMessage)
        self._worker.finished.connect(self._on_conversion_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_format_file(self, path: str) -> None:
        self.input_panel.set_processing(True)
        self._throbber.show()
        self.status_bar.showMessage("Formatting…")

        self._format_worker = FormatWorker([path])
        self._format_worker.progress.connect(self.status_bar.showMessage)
        self._format_worker.finished.connect(self._on_format_finished)
        self._format_worker.error.connect(self._on_error)
        self._format_worker.start()

    def _on_conversion_finished(self, markdown: str, saved_path: str) -> None:
        self._throbber.hide()
        if saved_path:
            self.output_panel.open_file(saved_path)
        else:
            self.output_panel.set_content(markdown)
        self.input_panel.set_processing(False)
        self.input_panel.refresh_output_tree()
        self.status_bar.showMessage("Done")

    def _on_format_finished(self, _content: str, saved_path: str) -> None:
        self._throbber.hide()
        if saved_path:
            self.output_panel.open_file(saved_path)
        self.input_panel.set_processing(False)
        self.input_panel.refresh_output_tree()
        self.status_bar.showMessage("Done")

    def _on_error(self, message: str) -> None:
        self._throbber.hide()
        self.input_panel.set_processing(False)
        self.status_bar.showMessage(f"Error: {message}")


def _ollama_running() -> bool:
    try:
        ollama.list()
        return True
    except Exception:
        return False
