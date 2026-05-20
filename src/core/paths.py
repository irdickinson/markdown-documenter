from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
