import sys

from PySide6.QtWidgets import QWidget

from tests.qt_test_utils import get_test_app

app = get_test_app()

dialog = RoutingDialog()

if dialog.exec():
    print(dialog.get_data())
else:
    print("Cancelled")