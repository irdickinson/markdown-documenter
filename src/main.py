import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.style import apply_stylesheet
from core.paths import ensure_dirs


def main() -> None:
    ensure_dirs()
    app = QApplication(sys.argv)
    app.setApplicationName("Markdown Documenter")
    apply_stylesheet(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
