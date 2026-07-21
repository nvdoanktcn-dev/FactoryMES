from PySide6.QtWidgets import (
    QTableWidget,
    QHeaderView,
    QAbstractItemView,
)


class DataTable(QTableWidget):
    def __init__(self):
        super().__init__()

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)

        self.verticalHeader().hide()

        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)