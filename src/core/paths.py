import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # Running inside a PyInstaller bundle — exe lives at dist/MarkdownDocumenter/
    PROJECT_ROOT = Path(sys.executable).parent
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

OUTPUT_DIR = PROJECT_ROOT / "output"


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
