from PyQt6.QtCore import QThread, pyqtSignal

from core.ai_formatter import reformat_with_doc_formatter
from core.formatter import format_youtube, format_web, safe_filename
from core.paths import OUTPUT_DIR
from core.web import extract_web
from core.youtube import extract_youtube

# output_mode values
RAW_ONLY = "raw_only"
FORMATTED_ONLY = "formatted_only"
BOTH = "both"


def _is_youtube_url(url: str) -> bool:
    return "youtube.com/watch" in url or "youtu.be/" in url


class ConversionWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, str)  # (markdown_content, saved_path)
    error = pyqtSignal(str)

    def __init__(
        self,
        sources: list[str],
        subfolder: str,
        output_mode: str = RAW_ONLY,
        formatting_mode: str = "structured",
    ) -> None:
        super().__init__()
        self.sources = sources
        self.subfolder = subfolder
        self.output_mode = output_mode
        self.formatting_mode = formatting_mode
        self._stopped = False

    def stop(self) -> None:
        self._stopped = True

    def run(self) -> None:
        base_dir = OUTPUT_DIR / self.subfolder if self.subfolder else OUTPUT_DIR
        raw_dir = base_dir / "raw"
        formatted_dir = base_dir / "formatted"

        if self.output_mode in (RAW_ONLY, BOTH):
            raw_dir.mkdir(parents=True, exist_ok=True)
        if self.output_mode in (FORMATTED_ONLY, BOTH):
            formatted_dir.mkdir(parents=True, exist_ok=True)

        last_markdown = ""
        last_saved = ""

        for i, source in enumerate(self.sources, 1):
            if self._stopped:
                self.progress.emit("Stopped.")
                break

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

            if self.output_mode in (RAW_ONLY, BOTH):
                raw_path = raw_dir / filename
                raw_path.write_text(markdown, encoding="utf-8")
                last_markdown = markdown
                last_saved = str(raw_path)
                self.progress.emit(f"[{i}/{len(self.sources)}] Saved raw: {filename}")

            if self.output_mode in (FORMATTED_ONLY, BOTH) and not self._stopped:
                self.progress.emit(
                    f"[{i}/{len(self.sources)}] Reformatting with doc-formatter ({self.formatting_mode})…"
                )
                try:
                    reformatted = reformat_with_doc_formatter(
                        markdown,
                        formatting_mode=self.formatting_mode,
                        stop_flag=lambda: self._stopped,
                    )
                    fmt_path = formatted_dir / filename
                    fmt_path.write_text(reformatted, encoding="utf-8")
                    last_markdown = reformatted
                    last_saved = str(fmt_path)
                    if self._stopped:
                        self.progress.emit(
                            f"[{i}/{len(self.sources)}] Stopped mid-format; partial output saved: {filename}"
                        )
                    else:
                        self.progress.emit(
                            f"[{i}/{len(self.sources)}] Formatted: {filename}"
                        )
                except Exception as exc:
                    if self.output_mode == FORMATTED_ONLY:
                        raw_dir.mkdir(parents=True, exist_ok=True)
                        raw_path = raw_dir / filename
                        raw_path.write_text(markdown, encoding="utf-8")
                        last_markdown = markdown
                        last_saved = str(raw_path)
                        self.progress.emit(
                            f"[{i}/{len(self.sources)}] doc-formatter failed ({exc}); saved raw instead"
                        )
                    else:
                        self.progress.emit(
                            f"[{i}/{len(self.sources)}] doc-formatter failed ({exc}); keeping raw output"
                        )

        self.finished.emit(last_markdown, last_saved)
