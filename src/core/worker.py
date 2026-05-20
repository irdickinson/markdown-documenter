from PyQt6.QtCore import QThread, pyqtSignal


class ConversionWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, str)  # (markdown_content, saved_path)
    error = pyqtSignal(str)

    def __init__(self, sources: list[str], subfolder: str) -> None:
        super().__init__()
        self.sources = sources
        self.subfolder = subfolder

    def run(self) -> None:
        # Stub — YouTube and web extraction implemented in later stages
        self.progress.emit("Processing (stub)…")
        placeholder = (
            "# Placeholder\n\n"
            "> Conversion not yet implemented.\n\n"
            f"**Sources queued:** {len(self.sources)}\n\n"
            + "\n".join(f"- {s}" for s in self.sources)
        )
        self.finished.emit(placeholder, "")
