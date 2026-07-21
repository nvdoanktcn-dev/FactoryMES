from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QWidget,
)


class ImportStatistics(QWidget):
    """
    Hiển thị thông tin preview Excel.

    Bao gồm:
    - Tổng số dòng
    - Tổng số cột
    - Dòng header
    - Thời gian đọc file
    """

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.rows_label = QLabel(
            "Rows: -"
        )

        self.columns_label = QLabel(
            "Columns: -"
        )

        self.header_label = QLabel(
            "Header: -"
        )

        self.duration_label = QLabel(
            "Time: -"
        )

        self._configure()
        self._build_ui()

    # ==========================================================
    # Setup
    # ==========================================================

    def _configure(self):
        labels = (
            self.rows_label,
            self.columns_label,
            self.header_label,
            self.duration_label,
        )

        for label in labels:
            label.setMinimumWidth(
                82
            )

            label.setStyleSheet(
                "font-size:11px;"
                "color:#546E7A;"
                "font-weight:bold;"
            )

    def _build_ui(self):
        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            10
        )

        layout.addWidget(
            self.rows_label
        )

        layout.addWidget(
            self.columns_label
        )

        layout.addWidget(
            self.header_label
        )

        layout.addWidget(
            self.duration_label
        )

    # ==========================================================
    # Public API
    # ==========================================================

    def update_preview_info(
        self,
        total_rows,
        total_columns,
        header_row,
        duration=None,
    ):
        self.rows_label.setText(
            f"Rows: {self._to_int(total_rows)}"
        )

        self.columns_label.setText(
            f"Columns: {self._to_int(total_columns)}"
        )

        header_index = self._to_int(
            header_row
        )

        self.header_label.setText(
            f"Header: {header_index + 1}"
        )

        if duration is None:
            duration_text = "-"
        else:
            try:
                duration_text = (
                    f"{float(duration):.3f}s"
                )

            except (
                TypeError,
                ValueError,
            ):
                duration_text = str(
                    duration
                )

        self.duration_label.setText(
            f"Time: {duration_text}"
        )

    def reset(self):
        self.rows_label.setText(
            "Rows: -"
        )

        self.columns_label.setText(
            "Columns: -"
        )

        self.header_label.setText(
            "Header: -"
        )

        self.duration_label.setText(
            "Time: -"
        )

    @staticmethod
    def _to_int(
        value,
    ):
        try:
            return int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0