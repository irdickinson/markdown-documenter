from PyQt6.QtCore import QThread, pyqtSignal

from core.formatter import format_youtube, format_web, safe_filename
from core.paths import OUTPUT_DIR
from core.web import extract_web
from core.youtube import extract_youtube


def _is_youtube_url(url: str) -> bool:
    return "youtube.com/watch" in url or "youtu.be/" in url


class ConversionWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, str)  # (markdown_content, saved_path)
    error = pyqtSignal(str)

    def __init__(self, sources: list[str], subfolder: str) -> None:
        super().__init__()
        self.sources = sources
        self.subfolder = subfolder

    def run(self) -> None:
        out_dir = OUTPUT_DIR / self.subfolder if self.subfolder else OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        last_markdown = ""
        last_saved = ""

        for i, source in enumerate(self.sources, 1):
            self.progress.emit(
                f"[{i}/{len(self.sources)}] Fetching {source[:70]}…"
            )
            try:
                if _is_youtube_url(source):
                    result = extract_youtube(source)
                    markdown = format_youtube(result)
                    title = result.title
                else:
                    result = extract_web(source)
                    markdown = format_web(result)
                    title = result.title
            except Exception as exc:
                self.error.emit(str(exc))
                return

            filename = safe_filename(title)
            save_path = out_dir / filename
            save_path.write_text(markdown, encoding="utf-8")
            last_markdown = markdown
            last_saved = str(save_path)
            self.progress.emit(f"[{i}/{len(self.sources)}] Saved: {filename}")

        self.finished.emit(last_markdown, last_saved)
