from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
    QLineEdit,
)

from src.services.product_service import ProductService


class ProductPage(QWidget):
    def __init__(self):
        super().__init__()

        self.product_service = ProductService()

        self.table = QTableWidget()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search product code or name...")
        self.search_box.textChanged.connect(self.load_products)

        layout = QVBoxLayout()

        title = QLabel("Product Management")
        title.setStyleSheet("font-size:24px;font-weight:bold;")

        button_layout = QHBoxLayout()

        btn_refresh = QPushButton("Refresh")
        btn_import = QPushButton("Import Product Excel")

        btn_refresh.clicked.connect(self.load_products)
        btn_import.clicked.connect(self.import_product_excel)

        button_layout.addWidget(btn_refresh)
        button_layout.addWidget(btn_import)
        button_layout.addStretch()

        layout.addWidget(title)
        layout.addLayout(button_layout)
        layout.addWidget(self.search_box)
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.load_products()

    def load_products(self):
        products = self.product_service.get_all_products()

         keyword = self.search_box.text().strip().lower()

    if keyword:
        products = [
            p for p in products
            if keyword in (p.product_code or "").lower()
            or keyword in (p.product_name_vi or "").lower()
            or keyword in (p.product_name_cn or "").lower()
        ]

    self.table.setColumnCount(6)
    self.table.setHorizontalHeaderLabels(
        [
            "Product Code",
            "Name VI",
            "Name CN",
            "Customer",
            "Material",
            "Status",
        ]
    )

    self.table.setRowCount(len(products))

    for row, product in enumerate(products):
        self.table.setItem(row, 0, QTableWidgetItem(product.product_code))
        self.table.setItem(row, 1, QTableWidgetItem(product.product_name_vi or ""))
        self.table.setItem(row, 2, QTableWidgetItem(product.product_name_cn or ""))
        self.table.setItem(row, 3, QTableWidgetItem(product.customer or ""))
        self.table.setItem(row, 4, QTableWidgetItem(product.material or ""))
        self.table.setItem(row, 5, QTableWidgetItem(product.status or ""))

    self.table.resizeColumnsToContents()

        self.table.setRowCount(len(products))

        for row, product in enumerate(products):
            self.table.setItem(row, 0, QTableWidgetItem(product.product_code))
            self.table.setItem(row, 1, QTableWidgetItem(product.product_name_vi or ""))
            self.table.setItem(row, 2, QTableWidgetItem(product.product_name_cn or ""))
            self.table.setItem(row, 3, QTableWidgetItem(product.customer or ""))
            self.table.setItem(row, 4, QTableWidgetItem(product.material or ""))
            self.table.setItem(row, 5, QTableWidgetItem(product.status or ""))

        self.table.resizeColumnsToContents()

    def import_product_excel(self):
        from src.importer.product_importer import ProductImporter

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Product Excel",
            "",
            "Excel Files (*.xlsx *.xlsm)"
        )

        if not file_path:
            return

        importer = ProductImporter()

        result = importer.import_excel(
            file_path=file_path,
            sheet_name="Product"
        )

        if result["success"]:
            QMessageBox.information(
                self,
                "Success",
                f"Imported {result['imported']} products."
            )
            self.load_products()
        else:
            QMessageBox.warning(
                self,
                "Error",
                "\n".join(result["errors"])
            )