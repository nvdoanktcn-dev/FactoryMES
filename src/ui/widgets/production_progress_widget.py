from __future__ import annotations

from enum import StrEnum
from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.services.progress_service import (
    ProgressItem,
    ProgressStatus,
)


class ProgressSortMode(StrEnum):
    WORK_ORDER = "work_order"
    PROGRESS = "progress"
    REMAINING = "remaining"


class ProductionProgressWidget(QWidget):
    """Hiển thị tiến độ sản xuất theo công lệnh."""

    STATUS_TEXT = {
        ProgressStatus.NOT_STARTED: "Chưa bắt đầu",
        ProgressStatus.IN_PROGRESS: "Đang sản xuất",
        ProgressStatus.ON_TRACK: "Gần hoàn thành",
        ProgressStatus.COMPLETED: "Hoàn thành",
        ProgressStatus.OVER_COMPLETED: "Vượt kế hoạch",
    }

    STATUS_STYLE = {
        ProgressStatus.NOT_STARTED: """
            QProgressBar::chunk {
                background-color: #9e9e9e;
            }
        """,
        ProgressStatus.IN_PROGRESS: """
            QProgressBar::chunk {
                background-color: #2196f3;
            }
        """,
        ProgressStatus.ON_TRACK: """
            QProgressBar::chunk {
                background-color: #43a047;
            }
        """,
        ProgressStatus.COMPLETED: """
            QProgressBar::chunk {
                background-color: #1b5e20;
            }
        """,
        ProgressStatus.OVER_COMPLETED: """
            QProgressBar::chunk {
                background-color: #f57c00;
            }
        """,
    }

    COLUMN_WORK_ORDER = 0
    COLUMN_PRODUCT = 1
    COLUMN_PROGRESS = 2
    COLUMN_COMPLETED = 3
    COLUMN_PLANNED = 4
    COLUMN_REMAINING = 5
    COLUMN_STATUS = 6

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._data: tuple[ProgressItem, ...] = ()
        self._display_data: tuple[ProgressItem, ...] = ()

        self._build_ui()
        self._connect_signals()
        self.clear()

    @property
    def data(self) -> tuple[ProgressItem, ...]:
        return self._data

    @property
    def display_data(self) -> tuple[ProgressItem, ...]:
        return self._display_data

    @property
    def sort_mode(self) -> ProgressSortMode:
        raw_value = self.sort_combo.currentData()

        try:
            return ProgressSortMode(raw_value)
        except (TypeError, ValueError):
            return ProgressSortMode.WORK_ORDER

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        toolbar_layout = QHBoxLayout()

        title_label = QLabel("Tiến độ sản xuất")
        title_label.setObjectName("progressTitle")

        sort_label = QLabel("Sắp xếp:")

        self.sort_combo = QComboBox()
        self.sort_combo.addItem(
            "Công lệnh",
            ProgressSortMode.WORK_ORDER,
        )
        self.sort_combo.addItem(
            "% hoàn thành",
            ProgressSortMode.PROGRESS,
        )
        self.sort_combo.addItem(
            "Số lượng còn lại",
            ProgressSortMode.REMAINING,
        )

        toolbar_layout.addWidget(title_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(sort_label)
        toolbar_layout.addWidget(self.sort_combo)

        root_layout.addLayout(toolbar_layout)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            [
                "Công lệnh",
                "Sản phẩm",
                "Tiến độ",
                "Hoàn thành",
                "Kế hoạch",
                "Còn lại",
                "Trạng thái",
            ]
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            self.COLUMN_WORK_ORDER,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            self.COLUMN_PRODUCT,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            self.COLUMN_PROGRESS,
            QHeaderView.ResizeMode.Stretch,
        )

        for column in (
            self.COLUMN_COMPLETED,
            self.COLUMN_PLANNED,
            self.COLUMN_REMAINING,
            self.COLUMN_STATUS,
        ):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        root_layout.addWidget(self.table, 1)

        self.empty_label = QLabel(
            "Không có dữ liệu tiến độ sản xuất."
        )
        self.empty_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.empty_label.setObjectName("progressEmptyLabel")

        root_layout.addWidget(self.empty_label)

        self.setStyleSheet(
            """
            QLabel#progressTitle {
                font-size: 16px;
                font-weight: 700;
            }

            QLabel#progressEmptyLabel {
                padding: 20px;
            }

            QProgressBar {
                min-height: 22px;
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                text-align: center;
                background-color: #eeeeee;
            }

            QProgressBar::chunk {
                border-radius: 3px;
            }
            """
        )

    def _connect_signals(self) -> None:
        self.sort_combo.currentIndexChanged.connect(
            self._on_sort_changed
        )

    def set_data(
        self,
        items: Iterable[ProgressItem] | None,
    ) -> None:
        self._data = tuple(items or ())
        self._refresh()

    def clear(self) -> None:
        self._data = ()
        self._display_data = ()
        self.table.setRowCount(0)
        self._update_empty_state(True)

    def set_sort_mode(
        self,
        mode: ProgressSortMode | str,
    ) -> None:
        try:
            resolved = ProgressSortMode(mode)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Chế độ sắp xếp không hợp lệ."
            ) from exc

        index = self.sort_combo.findData(resolved)

        if index < 0:
            raise ValueError(
                f"Không tìm thấy chế độ sắp xếp: {resolved}"
            )

        self.sort_combo.setCurrentIndex(index)

        # Khi index hiện tại không đổi, signal sẽ không phát.
        if self.sort_mode == resolved:
            self._refresh()

    def sort_by_work_order(self) -> None:
        self.set_sort_mode(
            ProgressSortMode.WORK_ORDER
        )

    def sort_by_progress(self) -> None:
        self.set_sort_mode(
            ProgressSortMode.PROGRESS
        )

    def sort_by_remaining(self) -> None:
        self.set_sort_mode(
            ProgressSortMode.REMAINING
        )

    def progress_bar_at(
        self,
        row: int,
    ) -> QProgressBar | None:
        widget = self.table.cellWidget(
            row,
            self.COLUMN_PROGRESS,
        )

        if isinstance(widget, QProgressBar):
            return widget

        return None

    def _on_sort_changed(
        self,
        index: int,
    ) -> None:
        del index
        self._refresh()

    def _refresh(self) -> None:
        self._display_data = tuple(
            self._sorted_items(self._data)
        )

        self.table.setRowCount(0)

        for item in self._display_data:
            self._append_row(item)

        self._update_empty_state(
            not self._display_data
        )

    def _sorted_items(
        self,
        items: Iterable[ProgressItem],
    ) -> list[ProgressItem]:
        result = list(items)

        if self.sort_mode == ProgressSortMode.PROGRESS:
            return sorted(
                result,
                key=lambda item: (
                    -item.progress_percent,
                    item.work_order,
                ),
            )

        if self.sort_mode == ProgressSortMode.REMAINING:
            return sorted(
                result,
                key=lambda item: (
                    -item.remaining_qty,
                    item.work_order,
                ),
            )

        return sorted(
            result,
            key=lambda item: item.work_order,
        )

    def _append_row(
        self,
        item: ProgressItem,
    ) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(
            row,
            self.COLUMN_WORK_ORDER,
            QTableWidgetItem(item.work_order),
        )
        self.table.setItem(
            row,
            self.COLUMN_PRODUCT,
            QTableWidgetItem(item.product),
        )

        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(
            round(item.display_percent)
        )
        progress_bar.setFormat(
            f"{item.progress_percent:.2f}%"
        )
        progress_bar.setProperty(
            "progress_status",
            item.status.value,
        )
        progress_bar.setStyleSheet(
            self.STATUS_STYLE[item.status]
        )

        self.table.setCellWidget(
            row,
            self.COLUMN_PROGRESS,
            progress_bar,
        )

        self._set_number_item(
            row,
            self.COLUMN_COMPLETED,
            item.completed_qty,
        )
        self._set_number_item(
            row,
            self.COLUMN_PLANNED,
            item.planned_qty,
        )
        self._set_number_item(
            row,
            self.COLUMN_REMAINING,
            item.remaining_qty,
        )

        status_item = QTableWidgetItem(
            self.STATUS_TEXT[item.status]
        )
        status_item.setData(
            Qt.ItemDataRole.UserRole,
            item.status.value,
        )

        self.table.setItem(
            row,
            self.COLUMN_STATUS,
            status_item,
        )

    def _set_number_item(
        self,
        row: int,
        column: int,
        value: int,
    ) -> None:
        table_item = QTableWidgetItem(
            f"{value:,}"
        )
        table_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )
        table_item.setData(
            Qt.ItemDataRole.UserRole,
            value,
        )

        self.table.setItem(
            row,
            column,
            table_item,
        )

    def _update_empty_state(
        self,
        empty: bool,
    ) -> None:
        self.empty_label.setVisible(empty)
        self.table.setVisible(not empty)