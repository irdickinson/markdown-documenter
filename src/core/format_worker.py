from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from core.ai_formatter import DEFAULT_MODEL, reformat_with_doc_formatter


class FormatWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, str)  # (content, saved_path)
    error = pyqtSignal(str)

    def __init__(
        self,
        paths: list[str],
        formatting_mode: str = "structured",
        model: str = DEFAULT_MODEL,
    ) -> None:
        super().__init__()
        self.paths = [Path(p) for p in paths]
        self.formatting_mode = formatting_mode
        self.model = model
        self._stopped = False

    def stop(self) -> None:
        self._stopped = True

    def run(self) -> None:
        last_content = ""
        last_saved = ""

        for i, src in enumerate(self.paths, 1):
            if self._stopped:
                self.progress.emit("Stopped.")
                break

            self.progress.emit(f"[{i}/{len(self.paths)}] Formatting {src.name}…")
            try:
                content = src.read_text(encoding="utf-8")
                reformatted = reformat_with_doc_formatter(
                    content,
                    formatting_mode=self.formatting_mode,
                    model=self.model,
                    stop_flag=lambda: self._stopped,
                )
                dest = _formatted_path(src)
                dest.write_text(reformatted, encoding="utf-8")
                last_content = reformatted
                last_saved = str(dest)
                if self._stopped:
                    self.progress.emit(
                        f"[{i}/{len(self.paths)}] Stopped; partial output saved: {dest.name}"
                    )
                else:
                    self.progress.emit(f"[{i}/{len(self.paths)}] Saved: {dest.name}")
            except Exception as exc:
                self.error.emit(str(exc))
                return

        self.finished.emit(last_content, last_saved)


def _formatted_path(src: Path) -> Path:
    if src.parent.name == "raw":
        target_dir = src.parent.parent / "formatted"
    elif src.parent.name == "formatted":
        target_dir = src.parent  # overwrite in-place
    else:
        target_dir = src.parent / "formatted"
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / src.name
