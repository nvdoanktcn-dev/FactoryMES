from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
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


class ProductDialog(QDialog):
    """Form dùng chung cho thao tác thêm và sửa sản phẩm."""

    def __init__(
        self,
        parent=None,
        *,
        product=None,
    ) -> None:
        super().__init__(parent)

        self.product = product
        self.setWindowTitle(
            "Add Product"
            if product is None
            else "Edit Product"
        )
        self.setMinimumWidth(440)

        self.product_code = QLineEdit()
        self.product_name_vi = QLineEdit()
        self.product_name_cn = QLineEdit()
        self.customer = QLineEdit()
        self.material = QLineEdit()

        self.unit = QComboBox()
        self.unit.setEditable(True)
        self.unit.addItems(
            [
                "PCS",
                "SET",
                "KG",
                "M",
            ]
        )

        self.status = QComboBox()
        self.status.addItems(
            [
                "ACTIVE",
                "INACTIVE",
            ]
        )

        form = QFormLayout()
        form.addRow("Product Code *", self.product_code)
        form.addRow("Name VI *", self.product_name_vi)
        form.addRow("Name CN", self.product_name_cn)
        form.addRow("Customer", self.customer)
        form.addRow("Material", self.material)
        form.addRow("Unit", self.unit)
        form.addRow("Status", self.status)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        if product is not None:
            self._load_product(product)

    def _load_product(self, product) -> None:
        self.product_code.setText(
            product.product_code or ""
        )
        self.product_code.setReadOnly(True)
        self.product_name_vi.setText(
            product.product_name_vi or ""
        )
        self.product_name_cn.setText(
            product.product_name_cn or ""
        )
        self.customer.setText(
            product.customer or ""
        )
        self.material.setText(
            product.material or ""
        )
        self.unit.setCurrentText(
            product.unit or "PCS"
        )
        self.status.setCurrentText(
            product.status or "ACTIVE"
        )

    def get_data(self) -> dict:
        return {
            "product_code": self.product_code.text(),
            "product_name_vi": self.product_name_vi.text(),
            "product_name_cn": self.product_name_cn.text(),
            "customer": self.customer.text(),
            "material": self.material.text(),
            "unit": self.unit.currentText(),
            "status": self.status.currentText(),
        }

    def accept(self) -> None:
        data = self.get_data()

        if not data["product_code"].strip():
            QMessageBox.warning(
                self,
                "Invalid Product",
                "Product Code is required.",
            )
            self.product_code.setFocus()
            return

        if not data["product_name_vi"].strip():
            QMessageBox.warning(
                self,
                "Invalid Product",
                "Vietnamese Name is required.",
            )
            self.product_name_vi.setFocus()
            return

        super().accept()


class ProductPage(QWidget):
    COLUMNS = [
        ("Product Code", "product_code"),
        ("Name VI", "product_name_vi"),
        ("Name CN", "product_name_cn"),
        ("Customer", "customer"),
        ("Material", "material"),
        ("Unit", "unit"),
        ("Status", "status"),
    ]

    def __init__(
        self,
        parent=None,
        product_service: ProductService | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName("ProductPage")

        self.product_service = (
            product_service
            if product_service is not None
            else ProductService()
        )
        self._resources_closed = False

        self.title_label = QLabel(
            "Product Management"
        )
        self.status_label = QLabel()
        self.table = QTableWidget()
        self.search_box = QLineEdit()

        self.btn_add = QPushButton("Add Product")
        self.btn_edit = QPushButton("Edit")
        self.btn_status = QPushButton("Deactivate")
        self.btn_refresh = QPushButton("Refresh")
        self.btn_import = QPushButton(
            "Import Product Excel"
        )

        self._build_ui()
        self._connect_signals()
        self._apply_style()
        self.load_products()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )
        layout.setSpacing(10)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.addWidget(self.btn_add)
        button_layout.addWidget(self.btn_edit)
        button_layout.addWidget(self.btn_status)
        button_layout.addWidget(self.btn_refresh)
        button_layout.addWidget(self.btn_import)
        button_layout.addStretch()

        self.search_box.setPlaceholderText(
            "Search product code, name, customer or material..."
        )
        self.search_box.setClearButtonEnabled(True)

        self.table.setColumnCount(
            len(self.COLUMNS)
        )
        self.table.setHorizontalHeaderLabels(
            [
                title
                for title, _ in self.COLUMNS
            ]
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setStretchLastSection(
            True
        )

        layout.addWidget(self.title_label)
        layout.addLayout(button_layout)
        layout.addWidget(self.search_box)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.status_label)

        self._update_action_buttons()

    def _apply_style(self) -> None:
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

        for button in (
            self.btn_add,
            self.btn_edit,
            self.btn_status,
            self.btn_refresh,
            self.btn_import,
        ):
            button.setMinimumHeight(32)

    def _connect_signals(self) -> None:
        self.btn_add.clicked.connect(
            self.add_product
        )
        self.btn_edit.clicked.connect(
            self.edit_selected_product
        )
        self.btn_status.clicked.connect(
            self.change_selected_status
        )
        self.btn_refresh.clicked.connect(
            self.load_products
        )
        self.btn_import.clicked.connect(
            self.import_product_excel
        )
        self.search_box.textChanged.connect(
            self.load_products
        )
        self.table.itemSelectionChanged.connect(
            self._update_action_buttons
        )
        self.table.itemDoubleClicked.connect(
            lambda _item: self.edit_selected_product()
        )

    def load_products(self, *_args) -> None:
        if self._resources_closed:
            return []

        keyword = self.search_box.text().strip()

        try:
            search_method = getattr(
                self.product_service,
                "search_products",
                None,
            )

            if callable(search_method):
                products = search_method(keyword)
            else:
                products = (
                    self.product_service.get_all_products()
                )
                lowered_keyword = keyword.lower()

                if lowered_keyword:
                    products = [
                        product
                        for product in products
                        if any(
                            lowered_keyword
                            in str(
                                getattr(
                                    product,
                                    attribute,
                                    "",
                                )
                                or ""
                            ).lower()
                            for _, attribute in self.COLUMNS
                        )
                    ]
        except Exception as error:
            self._show_error(
                "Load Products",
                error,
            )
            return []

        products = sorted(
            products,
            key=lambda product: str(
                product.product_code or ""
            ),
        )

        self.table.setSortingEnabled(False)
        self.table.setRowCount(
            len(products)
        )

        for row, product in enumerate(products):
            for column, (_, attribute) in enumerate(
                self.COLUMNS
            ):
                value = getattr(
                    product,
                    attribute,
                    "",
                )
                item = QTableWidgetItem(
                    str(value or "")
                )

                if column == 0:
                    item.setData(
                        Qt.UserRole,
                        product.product_code,
                    )

                if column in {0, 5, 6}:
                    item.setTextAlignment(
                        Qt.AlignCenter
                    )

                self.table.setItem(
                    row,
                    column,
                    item,
                )

        self.table.setSortingEnabled(True)
        self.table.resizeRowsToContents()
        self.status_label.setText(
            f"{len(products)} product record(s)."
        )
        self._update_action_buttons()

        return products

    def selected_product_code(self) -> str | None:
        selected_rows = (
            self.table.selectionModel().selectedRows()
        )

        if not selected_rows:
            return None

        row = selected_rows[0].row()
        item = self.table.item(row, 0)

        if item is None:
            return None

        return str(
            item.data(Qt.UserRole)
            or item.text()
            or ""
        ).strip()

    def selected_product(self):
        product_code = self.selected_product_code()

        if not product_code:
            return None

        return self.product_service.get_product(
            product_code
        )

    def add_product(self) -> None:
        dialog = ProductDialog(self)

        if dialog.exec() != QDialog.Accepted:
            return

        data = dialog.get_data()

        try:
            self.product_service.create_product(
                product_code=data["product_code"],
                product_name_vi=data["product_name_vi"],
                product_name_cn=data["product_name_cn"],
                customer=data["customer"],
                material=data["material"],
                unit=data["unit"],
                status=data["status"],
            )
            self.product_service.commit_changes()
        except Exception as error:
            self.product_service.rollback_changes()
            self._show_error(
                "Add Product",
                error,
            )
            return

        self.load_products()
        QMessageBox.information(
            self,
            "Success",
            "Product was created successfully.",
        )

    def edit_selected_product(self) -> None:
        product = self.selected_product()

        if product is None:
            QMessageBox.information(
                self,
                "Edit Product",
                "Select a product first.",
            )
            return

        product_code = product.product_code
        dialog = ProductDialog(
            self,
            product=product,
        )

        if dialog.exec() != QDialog.Accepted:
            return

        data = dialog.get_data()

        try:
            self.product_service.update_product(
                product_code,
                data,
            )
            self.product_service.commit_changes()
        except Exception as error:
            self.product_service.rollback_changes()
            self._show_error(
                "Edit Product",
                error,
            )
            return

        self.load_products()
        QMessageBox.information(
            self,
            "Success",
            "Product was updated successfully.",
        )

    def change_selected_status(self) -> None:
        product = self.selected_product()

        if product is None:
            QMessageBox.information(
                self,
                "Product Status",
                "Select a product first.",
            )
            return

        new_status = (
            "INACTIVE"
            if product.status == "ACTIVE"
            else "ACTIVE"
        )
        action = (
            "deactivate"
            if new_status == "INACTIVE"
            else "activate"
        )

        answer = QMessageBox.question(
            self,
            "Confirm Status",
            (
                f"Do you want to {action} "
                f"{product.product_code}?"
            ),
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self.product_service.set_product_status(
                product.product_code,
                new_status,
            )
            self.product_service.commit_changes()
        except Exception as error:
            self.product_service.rollback_changes()
            self._show_error(
                "Product Status",
                error,
            )
            return

        self.load_products()

    def _update_action_buttons(self) -> None:
        product = self.selected_product()
        has_selection = product is not None

        self.btn_edit.setEnabled(has_selection)
        self.btn_status.setEnabled(has_selection)

        if not has_selection:
            self.btn_status.setText("Deactivate")
            return

        self.btn_status.setText(
            "Deactivate"
            if product.status == "ACTIVE"
            else "Activate"
        )

    def import_product_excel(self) -> None:
        from src.importer.product_importer import (
            ProductImporter,
        )

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
            importer = ProductImporter()
            result = importer.import_excel(
                file_path=file_path,
                sheet_name="Product",
            )
        except Exception as error:
            self._show_error(
                "Import Product Excel",
                error,
            )
            return

        if result.get("success"):
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

        QMessageBox.warning(
            self,
            "Import Error",
            (
                "\n".join(
                    str(error)
                    for error in result.get(
                        "errors",
                        [],
                    )
                )
                or "Product import failed."
            ),
        )

    def _show_error(
        self,
        title: str,
        error: Exception,
    ) -> None:
        message = str(error)
        self.status_label.setText(message)
        QMessageBox.critical(
            self,
            title,
            message,
        )

    def on_page_activated(self) -> None:
        self.load_products()

    def close_resources(self) -> None:
        if self._resources_closed:
            return

        self._resources_closed = True
        close_method = getattr(
            self.product_service,
            "close",
            None,
        )

        if callable(close_method):
            close_method()

    def closeEvent(self, event) -> None:
        self.close_resources()
        super().closeEvent(event)
