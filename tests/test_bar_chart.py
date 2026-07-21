import sys

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)

from tests.qt_test_utils import get_test_app


def main():
    app = get_test_app()

    window = QWidget()
    layout = QHBoxLayout(window)

    # Tạo chart và các nút tại đây

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())