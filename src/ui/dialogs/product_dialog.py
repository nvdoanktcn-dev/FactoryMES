from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QHBoxLayout,
)


class ProductDialog(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)

        self.product = product

        if product is None:
            self.setWindowTitle("Add Product")
        else:
            self.setWindowTitle("Edit Product")

        self.resize(420, 320)

        self.product_code = QLineEdit()
        self.product_name_vi = QLineEdit()
        self.product_name_cn = QLineEdit()
        self.customer = QLineEdit()
        self.material = QLineEdit()
        self.unit = QLineEdit()
        self.status = QComboBox()

        self.status.addItems(["ACTIVE", "INACTIVE"])

        self.build_ui()

        if self.product is not None:
            self.load_product()

    def build_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        form.addRow("Product Code *", self.product_code)
        form.addRow("Vietnamese Name *", self.product_name_vi)
        form.addRow("Chinese Name", self.product_name_cn)
        form.addRow("Customer", self.customer)
        form.addRow("Material", self.material)
        form.addRow("Unit", self.unit)
        form.addRow("Status", self.status)

        button_layout = QHBoxLayout()

        btn_save = QPushButton("Save")
        btn_cancel = QPushButton("Cancel")

        btn_save.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(btn_save)
        button_layout.addWidget(btn_cancel)

        layout.addLayout(form)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_product(self):
        self.product_code.setText(self.product.product_code or "")
        self.product_code.setReadOnly(True)

        self.product_name_vi.setText(self.product.product_name_vi or "")
        self.product_name_cn.setText(self.product.product_name_cn or "")
        self.customer.setText(self.product.customer or "")
        self.material.setText(self.product.material or "")
        self.unit.setText(self.product.unit or "PCS")

        index = self.status.findText(self.product.status or "ACTIVE")
        if index >= 0:
            self.status.setCurrentIndex(index)

    def get_data(self):
        return {
            "product_code": self.product_code.text().strip(),
            "product_name_vi": self.product_name_vi.text().strip(),
            "product_name_cn": self.product_name_cn.text().strip(),
            "customer": self.customer.text().strip(),
            "material": self.material.text().strip(),
            "unit": self.unit.text().strip() or "PCS",
            "status": self.status.currentText(),
        }