import sys

from PySide6.QtWidgets import QWidget

from tests.qt_test_utils import get_test_app

app = get_test_app()

dialog = ProductionEntryDialog()

if dialog.exec():
    print(
        "Production Entry saved."
    )
else:
    print(
        "Production Entry cancelled."
    )