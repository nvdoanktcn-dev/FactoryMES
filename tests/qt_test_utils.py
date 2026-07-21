from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication


_APP: QApplication | None = None


def get_test_app() -> QApplication:
    """
    Trả về QApplication dùng chung cho toàn bộ test suite.

    Giữ reference toàn cục để QApplication không bị garbage collected.
    """
    global _APP

    app = QApplication.instance()

    if app is None:
        app = QApplication(sys.argv)

    _APP = app
    return app