from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class SortField(str, Enum):
    OEE = "OEE"
    AVAILABILITY = "Availability"
    PERFORMANCE = "Performance"
    QUALITY = "Quality"
    RUNTIME = "Runtime"
    DOWNTIME = "Downtime"
    OK_QTY = "OK Quantity"
    NG_QTY = "NG Quantity"


@dataclass
class MachineRow:
    machine: str
    oee: float = 0.0
    availability: float = 0.0
    performance: float = 0.0
    quality: float = 0.0
    runtime: float = 0.0
    downtime: float = 0.0
    ok_qty: int = 0
    ng_qty: int = 0


class TopMachineWidget(QWidget):
    """
    Hiển thị Top Machine theo nhiều tiêu chí.

    Widget này KHÔNG truy cập database.
    Widget này KHÔNG gọi service.

    Dữ liệu được truyền từ OEEDashboardController.
    """

    COLUMN_HEADERS = [
        "Rank",
        "Machine",
        "OEE %",
        "Runtime",
        "Downtime",
        "OK",
        "NG",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._rows: list[MachineRow] = []

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        title = QLabel("Top Machine")
        font = title.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 2)
        title.setFont(font)

        root.addWidget(title)

        toolbar = QHBoxLayout()

        toolbar.addWidget(QLabel("Sort by"))

        self.cbo_sort = QComboBox()
        self.cbo_sort.addItems(
            [
                SortField.OEE.value,
                SortField.AVAILABILITY.value,
                SortField.PERFORMANCE.value,
                SortField.QUALITY.value,
                SortField.RUNTIME.value,
                SortField.DOWNTIME.value,
                SortField.OK_QTY.value,
                SortField.NG_QTY.value,
            ]
        )

        toolbar.addWidget(self.cbo_sort)

        toolbar.addSpacing(20)

        toolbar.addWidget(QLabel("Top"))

        self.spin_top = QSpinBox()
        self.spin_top.setRange(1, 100)
        self.spin_top.setValue(10)

        toolbar.addWidget(self.spin_top)
        toolbar.addStretch()

        root.addLayout(toolbar)

        self.table = QTableWidget(0, len(self.COLUMN_HEADERS))

        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        root.addWidget(self.table)

    def _connect_signals(self) -> None:
        self.cbo_sort.currentIndexChanged.connect(self.refresh)
        self.spin_top.valueChanged.connect(self.refresh)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_data(self, rows: Iterable[Any]) -> None:
        """
        Nhận dữ liệu từ OEEDashboardController.

        rows có thể là:
            - list[MachineRow]
            - list[dict]
            - list[object]
        """

        self._rows.clear()

        for row in rows:
            self._rows.append(self._convert_row(row))

        self.refresh()

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Refresh bảng Top Machine."""

        rows = self._sorted_rows()

        limit = min(self.spin_top.value(), len(rows))

        self.table.setRowCount(limit)

        for rank, row in enumerate(rows[:limit], start=1):
            self._populate_row(rank - 1, rank, row)

        while self.table.rowCount() > limit:
            self.table.removeRow(limit)

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def _sorted_rows(self) -> list[MachineRow]:

        rows = list(self._rows)

        field = self.cbo_sort.currentText()

        key_map = {
            SortField.OEE.value:
                lambda r: r.oee,

            SortField.AVAILABILITY.value:
                lambda r: r.availability,

            SortField.PERFORMANCE.value:
                lambda r: r.performance,

            SortField.QUALITY.value:
                lambda r: r.quality,

            SortField.RUNTIME.value:
                lambda r: r.runtime,

            SortField.DOWNTIME.value:
                lambda r: r.downtime,

            SortField.OK_QTY.value:
                lambda r: r.ok_qty,

            SortField.NG_QTY.value:
                lambda r: r.ng_qty,
        }

        rows.sort(
            key=key_map.get(
                field,
                lambda r: r.oee,
            ),
            reverse=True,
        )

        return rows

    # ------------------------------------------------------------------
    # Data conversion
    # ------------------------------------------------------------------

    def _convert_row(self, row: Any) -> MachineRow:

        if isinstance(row, MachineRow):
            return row

        if isinstance(row, dict):
            return MachineRow(
                machine=str(
                    row.get("machine", "")
                ),
                oee=float(
                    row.get("oee", 0)
                ),
                availability=float(
                    row.get("availability", 0)
                ),
                performance=float(
                    row.get("performance", 0)
                ),
                quality=float(
                    row.get("quality", 0)
                ),
                runtime=float(
                    row.get("runtime", 0)
                ),
                downtime=float(
                    row.get("downtime", 0)
                ),
                ok_qty=int(
                    row.get("ok_qty", 0)
                ),
                ng_qty=int(
                    row.get("ng_qty", 0)
                ),
            )

        return MachineRow(
            machine=str(
                getattr(row, "machine", "")
            ),
            oee=float(
                getattr(row, "oee", 0)
            ),
            availability=float(
                getattr(row, "availability", 0)
            ),
            performance=float(
                getattr(row, "performance", 0)
            ),
            quality=float(
                getattr(row, "quality", 0)
            ),
            runtime=float(
                getattr(row, "runtime", 0)
            ),
            downtime=float(
                getattr(row, "downtime", 0)
            ),
            ok_qty=int(
                getattr(row, "ok_qty", 0)
            ),
            ng_qty=int(
                getattr(row, "ng_qty", 0)
            ),
        )

    # ------------------------------------------------------------------
    # Table rendering
    # ------------------------------------------------------------------

    def _populate_row(
        self,
        row_index: int,
        rank: int,
        row: MachineRow,
    ) -> None:

        self.table.setItem(
            row_index,
            0,
            self._text_item(str(rank), Qt.AlignmentFlag.AlignCenter),
        )

        self.table.setItem(
            row_index,
            1,
            self._text_item(row.machine),
        )

        oee_item = self._number_item(
            row.oee,
            decimals=2,
        )

        oee_item.setBackground(
            self._oee_color(row.oee)
        )

        self.table.setItem(
            row_index,
            2,
            oee_item,
        )

        self.table.setItem(
            row_index,
            3,
            self._number_item(
                row.runtime,
                decimals=2,
            ),
        )

        self.table.setItem(
            row_index,
            4,
            self._number_item(
                row.downtime,
                decimals=2,
            ),
        )

        self.table.setItem(
            row_index,
            5,
            self._integer_item(
                row.ok_qty,
            ),
        )

        self.table.setItem(
            row_index,
            6,
            self._integer_item(
                row.ng_qty,
            ),
        )

    # ------------------------------------------------------------------
    # Item helpers
    # ------------------------------------------------------------------

    def _text_item(
        self,
        text: str,
        alignment: Qt.AlignmentFlag = (
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        ),
    ) -> QTableWidgetItem:

        item = QTableWidgetItem(text)
        item.setTextAlignment(alignment)
        return item

    def _number_item(
        self,
        value: float,
        decimals: int = 2,
    ) -> QTableWidgetItem:

        item = QTableWidgetItem(
            f"{value:.{decimals}f}"
        )

        item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        return item

    def _integer_item(
        self,
        value: int,
    ) -> QTableWidgetItem:

        item = QTableWidgetItem(
            f"{int(value)}"
        )

        item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        return item

    # ------------------------------------------------------------------
    # Color helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _oee_color(
        oee: float,
    ) -> QColor:
        """
        OEE >= 85   : Green
        OEE >= 60   : Yellow
        OEE < 60    : Red
        """

        if oee >= 85:
            return QColor(198, 239, 206)

        if oee >= 60:
            return QColor(255, 235, 156)

        return QColor(255, 199, 206)