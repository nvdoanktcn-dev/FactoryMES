from PySide6.QtWidgets import QApplication


def get_test_app() -> QApplication:
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    return app