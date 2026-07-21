from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.services.product_service import ProductService


class ProductPage(QWidget):
    """
    Product Management Page.
    """

    HEADERS = [
        "Product Code",
        "Name VI",
        "Name CN",
        "Customer",
        "Material",
        "Unit",
        "Status",
    ]

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName(
            "ProductPage"
        )

        self.product_service = ProductService()

        self.title_label = QLabel(
            "Product Management",
            self,
        )

        self.search_box = QLineEdit(
            self
        )
        self.search_box.setPlaceholderText(
            "Search product code, name, customer or material..."
        )

        self.btn_refresh = QPushButton(
            "Refresh",
            self,
        )

        self.btn_import = QPushButton(
            "Import Product Excel",
            self,
        )

        self.table = QTableWidget(
            self
        )

        self.status_label = QLabel(
            "",
            self,
        )

        self._build_ui()
        self._configure_table()
        self._connect_events()
        self._apply_style()

        self.load_products()

    def _build_ui(self):
        root_layout = QVBoxLayout(
            self
        )

        root_layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )

        root_layout.setSpacing(
            10
        )

        button_layout = QHBoxLayout()
        button_layout.setSpacing(
            8
        )

        button_layout.addWidget(
            self.btn_refresh
        )

        button_layout.addWidget(
            self.btn_import
        )

        button_layout.addStretch()

        root_layout.addWidget(
            self.title_label
        )

        root_layout.addLayout(
            button_layout
        )

        root_layout.addWidget(
            self.search_box
        )

        root_layout.addWidget(
            self.table,
            1,
        )

        root_layout.addWidget(
            self.status_label
        )

    def _configure_table(self):
        self.table.setColumnCount(
            len(self.HEADERS)
        )

        self.table.setHorizontalHeaderLabels(
            self.HEADERS
        )

        self.table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.verticalHeader().setVisible(
            False
        )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        header.setStretchLastSection(
            True
        )

    def _connect_events(self):
        self.search_box.textChanged.connect(
            self.load_products
        )

        self.btn_refresh.clicked.connect(
            self.load_products
        )

        self.btn_import.clicked.connect(
            self.import_product_excel
        )

    def _apply_style(self):
        self.title_label.setStyleSheet(
            (
                "font-size:24px;"
                "font-weight:bold;"
                "color:#263238;"
            )
        )

        self.status_label.setStyleSheet(
            "color:#546E7A;"
        )

        self.btn_refresh.setMinimumHeight(
            32
        )

        self.btn_import.setMinimumHeight(
            32
        )

    def load_products(self):
        try:
            products = (
                self.product_service
                .get_all_products()
            )

            keyword = (
                self.search_box
                .text()
                .strip()
                .lower()
            )

            if keyword:
                products = [
                    product
                    for product in products
                    if (
                        keyword
                        in str(
                            product.product_code
                            or ""
                        ).lower()
                        or keyword
                        in str(
                            product.product_name_vi
                            or ""
                        ).lower()
                        or keyword
                        in str(
                            product.product_name_cn
                            or ""
                        ).lower()
                        or keyword
                        in str(
                            product.customer
                            or ""
                        ).lower()
                        or keyword
                        in str(
                            product.material
                            or ""
                        ).lower()
                    )
                ]

            products = sorted(
                products,
                key=lambda product: str(
                    product.product_code
                    or ""
                ),
            )

            self.table.setRowCount(
                len(products)
            )

            for row_index, product in enumerate(
                products
            ):
                values = [
                    product.product_code,
                    product.product_name_vi,
                    product.product_name_cn,
                    product.customer,
                    product.material,
                    getattr(
                        product,
                        "unit",
                        "",
                    ),
                    product.status,
                ]

                for column_index, value in enumerate(
                    values
                ):
                    item = QTableWidgetItem(
                        str(
                            value
                            if value is not None
                            else ""
                        )
                    )

                    if column_index in {
                        0,
                        5,
                        6,
                    }:
                        item.setTextAlignment(
                            Qt.AlignCenter
                        )

                    self.table.setItem(
                        row_index,
                        column_index,
                        item,
                    )

            self.table.resizeRowsToContents()

            self.status_label.setText(
                f"{len(products)} product record(s)."
            )

            return products

        except Exception as error:
            self.show_error(
                error
            )
            return []

    def import_product_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Product Excel",
            "",
            (
                "Excel Files (*.xlsx *.xls *.xlsm);;"
                "All Files (*.*)"
            ),
        )

        if not file_path:
            return

        try:
            from src.importer.product_importer import (
                ProductImporter,
            )

            importer = ProductImporter()

            result = importer.import_excel(
                file_path=file_path,
                sheet_name="Product",
            )

            if result.get(
                "success"
            ):
                QMessageBox.information(
                    self,
                    "Success",
                    (
                        f"Imported "
                        f"{result.get('imported', 0)} "
                        "products."
                    ),
                )

                self.load_products()
                return

            errors = result.get(
                "errors",
                [],
            )

            QMessageBox.warning(
                self,
                "Import Error",
                (
                    "\n".join(
                        str(error)
                        for error in errors
                    )
                    or "Product import failed."
                ),
            )

        except Exception as error:
            self.show_error(
                error
            )

    def on_page_activated(self):
        self.load_products()

    def closeEvent(
        self,
        event,
    ):
        close_method = getattr(
            self.product_service,
            "close",
            None,
        )

        if callable(
            close_method
        ):
            close_method()

        super().closeEvent(
            event
        )

    def show_error(
        self,
        error,
    ):
        message = str(
            error
        )

        self.status_label.setText(
            message
        )

        QMessageBox.warning(
            self,
            "Product Error",
            message,
        )
