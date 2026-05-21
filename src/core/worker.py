from PyQt6.QtCore import QThread, pyqtSignal

from core.ai_formatter import reformat_with_doc_formatter
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

    def __init__(
        self, sources: list[str], subfolder: str, use_doc_formatter: bool = False
    ) -> None:
        super().__init__()
        self.sources = sources
        self.subfolder = subfolder
        self.use_doc_formatter = use_doc_formatter

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

            if self.use_doc_formatter:
                self.progress.emit(
                    f"[{i}/{len(self.sources)}] Reformatting with doc-formatter…"
                )
                try:
                    reformatted = reformat_with_doc_formatter(markdown)
                    save_path.write_text(reformatted, encoding="utf-8")
                    last_markdown = reformatted
                    self.progress.emit(
                        f"[{i}/{len(self.sources)}] Stage 2 complete: {filename}"
                    )
                except Exception as exc:
                    # Non-fatal: Stage 1 file is already saved; report and continue
                    self.progress.emit(
                        f"[{i}/{len(self.sources)}] doc-formatter failed ({exc}); keeping Stage 1 output"
                    )

        self.finished.emit(last_markdown, last_saved)
