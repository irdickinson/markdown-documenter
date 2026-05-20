import ollama
from PyQt6.QtCore import QThread, pyqtSignal


class OllamaChatWorker(QThread):
    token = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, messages: list[dict], model: str) -> None:
        super().__init__()
        self.messages = messages
        self.model = model
        self._stopped = False

    def stop(self) -> None:
        self._stopped = True

    def run(self) -> None:
        try:
            stream = ollama.chat(
                model=self.model,
                messages=self.messages,
                stream=True,
            )
            for chunk in stream:
                if self._stopped:
                    break
                content = chunk.message.content
                if content:
                    self.token.emit(content)
            self.finished.emit()
        except Exception as exc:
            self.error.emit(str(exc))
