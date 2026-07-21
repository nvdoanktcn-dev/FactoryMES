from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
)

from src.ui.widgets.search_bar import SearchBar
from src.ui.widgets.toolbar import Toolbar
from src.ui.widgets.data_table import DataTable
from src.ui.widgets.summary_card import SummaryCard


class BasePage(QWidget):
    def __init__(self, title, search_placeholder="Search..."):
        super().__init__()

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size:24px;font-weight:bold;")

        self.card_total = SummaryCard("Total", "0", "#1976D2", "📦")
        self.card_active = SummaryCard("Active", "0", "#2ECC71", "🟢")
        self.card_inactive = SummaryCard("Inactive", "0", "#E74C3C", "🔴")

        self.search_bar = SearchBar(search_placeholder)
        self.toolbar = Toolbar()
        self.table = DataTable()
        self.status_label = QLabel()

        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout()

        card_layout = QHBoxLayout()
        card_layout.addWidget(self.card_total)
        card_layout.addWidget(self.card_active)
        card_layout.addWidget(self.card_inactive)

        layout.addWidget(self.title_label)
        layout.addLayout(card_layout)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.table)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def setup_table(self, headers):
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

    def set_headers(self, headers):
        self.setup_table(headers)

    def clear_table(self):
        self.table.setRowCount(0)

    def set_status(self, text):
        self.status_label.setText(text)

    def update_summary(self, total, active, inactive):
        self.card_total.set_value(total)
        self.card_active.set_value(active)
        self.card_inactive.set_value(inactive)

    def get_selected_row(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return row

    def get_selected_value(self, column_index):
        row = self.get_selected_row()
        if row is None:
            return None

        item = self.table.item(row, column_index)
        if item is None:
            return None

        return item.text()

    def show_info(self, title, message):
        QMessageBox.information(self, title, message)

    def show_warning(self, title, message):
        QMessageBox.warning(self, title, message)

    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)

    def confirm(
        self,
        title,
        message,
    ):
        result = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        return result == QMessageBox.Yes

    def refresh_table(self):
        pass