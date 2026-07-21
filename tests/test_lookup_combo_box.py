import sys

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
)

from src.ui.widgets.lookup_combo_box import LookupComboBox
from tests.qt_test_utils import get_test_app

app = get_test_app()


class DemoProduct:
    def __init__(
        self,
        product_code,
        product_name_vi,
    ):
        self.product_code = product_code
        self.product_name_vi = product_name_vi


products = [
    DemoProduct(
        "P001",
        "Sản phẩm A",
    ),
    DemoProduct(
        "P002",
        "Sản phẩm B",
    ),
    DemoProduct(
        "P003",
        "Sản phẩm C",
    ),
]


from tests.qt_test_utils import get_test_app

app = get_test_app()
def main():
    window = QWidget()
    window.setWindowTitle("LookupComboBox Test")
    window.resize(400, 160)

    layout = QVBoxLayout(window)

    combo = LookupComboBox(
        placeholder="-- Select Product --"
    )

    combo.set_items(
        products,
        key_getter=lambda p: p.product_code,
        text_getter=lambda p: (
            f"{p.product_code} - {p.product_name_vi}"
        ),
    )

    combo.value_changed.connect(
        lambda value: print(
            "Selected value:",
            value,
            "| Object:",
            combo.current_object(),
        )
    )

    layout.addWidget(combo)

    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())