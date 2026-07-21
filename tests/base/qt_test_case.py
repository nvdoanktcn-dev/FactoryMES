from __future__ import annotations

import unittest

from PySide6.QtWidgets import QApplication, QWidget

from tests.qt_test_utils import get_test_app


class QtTestCase(unittest.TestCase):
    app: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.app = get_test_app()

    def process_events(self) -> None:
        self.app.processEvents()

    def dispose_widget(self, widget: QWidget | None) -> None:
        if widget is None:
            return

        widget.close()
        widget.deleteLater()
        self.process_events()