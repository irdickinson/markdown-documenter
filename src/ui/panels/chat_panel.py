import markdown as md
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QPalette, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.chat_worker import OllamaChatWorker


class ChatPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._history: list[dict] = []
        self._streaming_text = ""
        self._worker: OllamaChatWorker | None = None
        self._build_ui()
        self._connect_signals()
        self.refresh_models()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh_models(self) -> None:
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
        except Exception:
            self._model_combo.addItem("llama3.1:8b")

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        # Model row
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self._model_combo = QComboBox()
        self._model_combo.setMinimumWidth(180)
        self._refresh_btn = QToolButton()
        self._refresh_btn.setText("↻")
        self._refresh_btn.setToolTip("Refresh model list from Ollama")
        self._clear_btn = QPushButton("Clear Chat")
        self._clear_btn.setObjectName("secondaryBtn")
        model_row.addWidget(self._model_combo)
        model_row.addWidget(self._refresh_btn)
        model_row.addStretch()
        model_row.addWidget(self._clear_btn)
        layout.addLayout(model_row)

        # Conversation display
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._browser.setPlaceholderText(
            "Start a conversation with your local Ollama model.\n\n"
            "Type a message below and press Enter or Send."
        )
        layout.addWidget(self._browser, stretch=1)

        # Separator above input area
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a message… (Enter to send)")
        self._send_btn = QPushButton("Send")
        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setObjectName("stopBtn")
        self._stop_btn.setEnabled(False)
        input_row.addWidget(self._input, stretch=1)
        input_row.addWidget(self._send_btn)
        input_row.addWidget(self._stop_btn)
        layout.addLayout(input_row)

    def _connect_signals(self) -> None:
        self._send_btn.clicked.connect(self._on_send)
        self._stop_btn.clicked.connect(self._on_stop)
        self._clear_btn.clicked.connect(self._on_clear)
        self._refresh_btn.clicked.connect(self.refresh_models)
        self._input.returnPressed.connect(self._on_send)
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self._on_send)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_send(self) -> None:
        text = self._input.text().strip()
        if not text or self._worker is not None:
            return
        model = self._model_combo.currentText().strip()
        if not model:
            QMessageBox.warning(self, "No Model", "Select an Ollama model first.")
            return

        self._input.clear()
        self._history.append({"role": "user", "content": text})
        self._streaming_text = ""
        self._render()

        self._set_busy(True)
        self._worker = OllamaChatWorker(list(self._history), model)
        self._worker.token.connect(self._on_token)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_stop(self) -> None:
        if self._worker:
            self._worker.stop()

    def _on_clear(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait()
            self._worker = None
        self._history.clear()
        self._streaming_text = ""
        self._browser.clear()
        self._set_busy(False)

    def _on_token(self, token: str) -> None:
        self._streaming_text += token
        self._render()

    def _on_finished(self) -> None:
        if self._streaming_text:
            self._history.append({"role": "assistant", "content": self._streaming_text})
            self._streaming_text = ""
        self._worker = None
        self._set_busy(False)
        self._render()

    def _on_error(self, message: str) -> None:
        self._streaming_text = ""
        self._worker = None
        self._set_busy(False)
        QMessageBox.warning(self, "Ollama Error", message)
        self._render()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _render(self) -> None:
        css = _build_css()
        body = ""
        for msg in self._history:
            if msg["role"] == "user":
                body += (
                    f'<div class="user-msg">'
                    f'<span class="label">You</span><br>'
                    f'{_esc(msg["content"])}'
                    f'</div>'
                )
            else:
                rendered = md.markdown(msg["content"], extensions=["extra", "nl2br"])
                body += (
                    f'<div class="ai-msg">'
                    f'<span class="label">Assistant</span><br>'
                    f'{rendered}'
                    f'</div>'
                )
        if self._streaming_text:
            rendered = md.markdown(self._streaming_text, extensions=["extra", "nl2br"])
            body += (
                f'<div class="ai-msg streaming">'
                f'<span class="label">Assistant</span><br>'
                f'{rendered}'
                f'</div>'
            )
        self._browser.setHtml(f"<html><head>{css}</head><body>{body}</body></html>")
        sb = self._browser.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _set_busy(self, busy: bool) -> None:
        self._send_btn.setEnabled(not busy)
        self._input.setEnabled(not busy)
        self._stop_btn.setEnabled(busy)
        if not busy:
            self._input.setFocus()


def _build_css() -> str:
    palette = QApplication.instance().palette()
    bg = palette.color(QPalette.ColorRole.Base)
    dark = bg.lightness() < 128

    if dark:
        text        = "#e8e8e8"
        user_bg     = "#1e3a5f"
        ai_bg       = "#2a2a2a"
        label_color = "#888"
        code_bg     = "#1a1a1a"
        border      = "#444"
    else:
        text        = "#1a1a1a"
        user_bg     = "#dbeafe"
        ai_bg       = "#f3f4f6"
        label_color = "#666"
        code_bg     = "#f4f4f4"
        border      = "#e0e0e0"

    return f"""<style>
body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    line-height: 1.6;
    color: {text};
    margin: 0; padding: 0;
}}
.user-msg, .ai-msg {{
    border-radius: 6px;
    padding: 10px 14px;
    margin: 6px 0;
    border: 1px solid {border};
}}
.user-msg {{ background: {user_bg}; }}
.ai-msg   {{ background: {ai_bg}; }}
.label    {{ font-size: 10px; color: {label_color}; text-transform: uppercase; letter-spacing: 0.05em; }}
p {{ margin: 4px 0; }}
code {{ background: {code_bg}; padding: 1px 4px; border-radius: 3px; font-family: Consolas, monospace; }}
pre  {{ background: {code_bg}; padding: 10px; border-radius: 4px; white-space: pre-wrap; word-break: break-word; }}
ul {{ padding-left: 20px; }} li {{ margin-bottom: 3px; }}
</style>"""


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
