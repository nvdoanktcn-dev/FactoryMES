from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QLabel,
    QVBoxLayout,
)


class ProductionKPIWidget(QFrame):
    """
    Hiển thị KPI Preview của Production Entry.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFrameShape(
            QFrame.StyledPanel
        )

        self.setObjectName(
            "ProductionKPIWidget"
        )

        self.setStyleSheet("""
            QFrame#ProductionKPIWidget {
                border: 1px solid #CFD8DC;
                border-radius: 8px;
                background: #FAFAFA;
            }

            QLabel {
                padding: 3px;
            }
        """)

        self.runtime_value = QLabel("-")
        self.net_runtime_value = QLabel("-")
        self.standard_cycle_value = QLabel("-")
        self.actual_cycle_value = QLabel("-")
        self.output_value = QLabel("-")
        self.yield_value = QLabel("-")
        self.performance_value = QLabel("-")
        self.ng_rate_value = QLabel("-")
        self.downtime_value = QLabel("-")

        self._value_labels = [
            self.runtime_value,
            self.net_runtime_value,
            self.standard_cycle_value,
            self.actual_cycle_value,
            self.output_value,
            self.yield_value,
            self.performance_value,
            self.ng_rate_value,
            self.downtime_value,
        ]

        for label in self._value_labels:
            label.setStyleSheet(
                "font-weight:bold;"
            )

        self.build_ui()
        self.clear_values()

    def build_ui(self):
        root_layout = QVBoxLayout(self)

        title = QLabel(
            "Production KPI Preview"
        )
        title.setStyleSheet(
            "font-size:16px;"
            "font-weight:bold;"
        )

        form = QFormLayout()

        form.addRow(
            "Runtime",
            self.runtime_value,
        )

        form.addRow(
            "Net Runtime",
            self.net_runtime_value,
        )

        form.addRow(
            "Standard Cycle",
            self.standard_cycle_value,
        )

        form.addRow(
            "Actual Cycle",
            self.actual_cycle_value,
        )

        form.addRow(
            "Output / Hour",
            self.output_value,
        )

        form.addRow(
            "Yield",
            self.yield_value,
        )

        form.addRow(
            "Performance",
            self.performance_value,
        )

        form.addRow(
            "NG Rate",
            self.ng_rate_value,
        )

        form.addRow(
            "Downtime",
            self.downtime_value,
        )

        root_layout.addWidget(title)
        root_layout.addLayout(form)

    def set_calculation(self, calculation):
        """
        Nhận ProductionCalculationResult.
        """
        if calculation is None:
            self.clear_values()
            return

        self.runtime_value.setText(
            self.format_duration(
                calculation.runtime_sec
            )
        )

        self.net_runtime_value.setText(
            self.format_duration(
                calculation.net_runtime_sec
            )
        )

        self.standard_cycle_value.setText(
            (
                f"{calculation.standard_cycle_time_sec:.3f} "
                "sec/PCS"
            )
        )

        self.actual_cycle_value.setText(
            (
                f"{calculation.actual_cycle_time_sec:.3f} "
                "sec/PCS"
            )
        )

        self.output_value.setText(
            (
                f"{calculation.output_per_hour:.2f} "
                "PCS/H"
            )
        )

        self.yield_value.setText(
            f"{calculation.yield_percent:.2f}%"
        )

        self.performance_value.setText(
            (
                f"{calculation.performance_percent:.2f}%"
            )
        )

        self.ng_rate_value.setText(
            f"{calculation.ng_percent:.2f}%"
        )

        self.downtime_value.setText(
            (
                f"{calculation.downtime_percent:.2f}%"
            )
        )

        self.apply_status_styles(
            calculation
        )

    def apply_status_styles(
        self,
        calculation,
    ):
        self._set_percent_style(
            self.yield_value,
            calculation.yield_percent,
            good_threshold=95.0,
            warning_threshold=90.0,
        )

        self._set_percent_style(
            self.performance_value,
            calculation.performance_percent,
            good_threshold=85.0,
            warning_threshold=70.0,
        )

        self._set_reverse_percent_style(
            self.ng_rate_value,
            calculation.ng_percent,
            good_threshold=3.0,
            warning_threshold=5.0,
        )

        self._set_reverse_percent_style(
            self.downtime_value,
            calculation.downtime_percent,
            good_threshold=10.0,
            warning_threshold=15.0,
        )

    def clear_values(self):
        for label in self._value_labels:
            label.setText("-")
            label.setStyleSheet(
                "font-weight:bold;"
                "color:#455A64;"
            )

    @staticmethod
    def format_duration(seconds):
        seconds = max(
            float(seconds or 0),
            0.0,
        )

        total_minutes = seconds / 60

        if total_minutes < 60:
            return f"{total_minutes:.2f} min"

        return (
            f"{seconds / 3600:.2f} hour"
        )

    @staticmethod
    def _set_percent_style(
        label,
        value,
        good_threshold,
        warning_threshold,
    ):
        value = float(value or 0)

        if value >= good_threshold:
            color = "#2E7D32"

        elif value >= warning_threshold:
            color = "#EF6C00"

        else:
            color = "#C62828"

        label.setStyleSheet(
            f"font-weight:bold;color:{color};"
        )

    @staticmethod
    def _set_reverse_percent_style(
        label,
        value,
        good_threshold,
        warning_threshold,
    ):
        value = float(value or 0)

        if value <= good_threshold:
            color = "#2E7D32"

        elif value <= warning_threshold:
            color = "#EF6C00"

        else:
            color = "#C62828"

        label.setStyleSheet(
            f"font-weight:bold;color:{color};"
        )