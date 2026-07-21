from abc import abstractmethod

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from src.ui.charts.chart_canvas import (
    ChartCanvas,
)


class BaseChart(QFrame):
    """
    Lớp nền cho các biểu đồ Dashboard.

    Chức năng chung:
    - Tiêu đề.
    - Subtitle.
    - ChartCanvas.
    - Empty State.
    - Refresh.
    - Clear.
    - Save Image.

    Lớp con cần triển khai:
        plot()
    """

    def __init__(
        self,
        title="Chart",
        subtitle="",
        parent=None,
    ):
        super().__init__(parent)

        self._title = str(title or "")
        self._subtitle = str(
            subtitle or ""
        )

        self._data = None
        self._has_data = False

        self.setObjectName(
            "BaseChart"
        )

        self.setMinimumHeight(340)

        self.title_label = QLabel(
            self._title
        )

        self.subtitle_label = QLabel(
            self._subtitle
        )

        self.btn_refresh = QPushButton(
            "Refresh"
        )

        self.canvas = ChartCanvas(
            parent=self
        )

        self.empty_label = QLabel(
            "No data available."
        )

        self.build_ui()
        self.connect_events()
        self.apply_style()

        self.show_empty_state()

    # ==========================================================
    # UI
    # ==========================================================

    def build_ui(self):
        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(
            12,
            10,
            12,
            10,
        )

        root_layout.setSpacing(8)

        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        self.title_label.setStyleSheet(
            "font-size:16px;"
            "font-weight:bold;"
            "color:#263238;"
        )

        self.subtitle_label.setStyleSheet(
            "font-size:11px;"
            "color:#78909C;"
        )

        title_layout.addWidget(
            self.title_label
        )

        title_layout.addWidget(
            self.subtitle_label
        )

        header_layout.addLayout(
            title_layout
        )

        header_layout.addStretch()

        self.btn_refresh.setMaximumWidth(
            90
        )

        header_layout.addWidget(
            self.btn_refresh
        )

        self.empty_label.setAlignment(
            Qt.AlignCenter
        )

        self.empty_label.setStyleSheet(
            "font-size:14px;"
            "color:#90A4AE;"
        )

        root_layout.addLayout(
            header_layout
        )

        root_layout.addWidget(
            self.canvas,
            1,
        )

        root_layout.addWidget(
            self.empty_label,
            1,
        )

    def apply_style(self):
        self.setStyleSheet("""
            QFrame#BaseChart {
                background: #FFFFFF;
                border: 1px solid #CFD8DC;
                border-radius: 8px;
            }

            QPushButton {
                min-height: 28px;
                padding: 4px 10px;
            }
        """)

    def connect_events(self):
        self.btn_refresh.clicked.connect(
            self.refresh_chart
        )

    # ==========================================================
    # Public API
    # ==========================================================

    def set_data(self, data):
        """
        Nạp dữ liệu vào biểu đồ.

        Lớp con có thể nhận:
        - list
        - dict
        - tuple
        - dataclass
        """
        self._data = data

        self._has_data = (
            not self.is_empty_data(data)
        )

        self.refresh_chart()

    def load_data(self, data):
        """
        Alias cho set_data().
        """
        self.set_data(data)

    def refresh_chart(self):
        """
        Refresh biểu đồ từ dữ liệu hiện tại.
        """
        if not self._has_data:
            self.show_empty_state()
            return

        try:
            self.show_chart()

            self.canvas.reset_axes()

            self.plot(
                self.canvas.axes,
                self._data,
            )

            self.apply_common_axes_style(
                self.canvas.axes
            )

            self.canvas.refresh()

        except Exception as error:
            self.show_error_state(
                str(error)
            )

    def clear_chart(self):
        self._data = None
        self._has_data = False

        self.canvas.clear()
        self.show_empty_state()

    def save_chart(
        self,
        file_path,
        dpi=150,
    ):
        if not self._has_data:
            raise ValueError(
                "There is no chart data to save."
            )

        self.canvas.save_chart(
            file_path=file_path,
            dpi=dpi,
        )

    def set_title(self, title):
        self._title = str(
            title or ""
        )

        self.title_label.setText(
            self._title
        )

    def set_subtitle(self, subtitle):
        self._subtitle = str(
            subtitle or ""
        )

        self.subtitle_label.setText(
            self._subtitle
        )

    # ==========================================================
    # State
    # ==========================================================

    def show_chart(self):
        self.canvas.setVisible(True)
        self.empty_label.setVisible(False)

    def show_empty_state(
        self,
        message="No data available.",
    ):
        self.canvas.setVisible(False)

        self.empty_label.setText(
            message
        )

        self.empty_label.setVisible(True)

    def show_error_state(
        self,
        message,
    ):
        self.canvas.setVisible(False)

        self.empty_label.setText(
            "Chart Error:\n"
            + str(message)
        )

        self.empty_label.setStyleSheet(
            "font-size:13px;"
            "font-weight:bold;"
            "color:#C62828;"
        )

        self.empty_label.setVisible(True)

    # ==========================================================
    # Axes styling
    # ==========================================================

    @staticmethod
    def apply_common_axes_style(
        axes,
    ):
        axes.grid(
            True,
            axis="y",
            alpha=0.25,
        )

        axes.spines[
            "top"
        ].set_visible(False)

        axes.spines[
            "right"
        ].set_visible(False)

        axes.tick_params(
            axis="x",
            labelrotation=0,
        )

    # ==========================================================
    # Data helpers
    # ==========================================================

    @staticmethod
    def is_empty_data(data):
        if data is None:
            return True

        if isinstance(
            data,
            (list, tuple, set, dict),
        ):
            return len(data) == 0

        return False

    @staticmethod
    def value_from(
        source,
        field_name,
        default=None,
    ):
        """
        Đọc giá trị từ dictionary hoặc object.
        """
        if source is None:
            return default

        if isinstance(source, dict):
            value = source.get(
                field_name,
                default,
            )

        else:
            value = getattr(
                source,
                field_name,
                default,
            )

        if value is None:
            return default

        return value

    @staticmethod
    def normalize_number(
        value,
        default=0.0,
    ):
        try:
            return float(
                value
                if value is not None
                else default
            )

        except (
            TypeError,
            ValueError,
        ):
            return float(default)

    # ==========================================================
    # Abstract API
    # ==========================================================

    @abstractmethod
    def plot(
        self,
        axes,
        data,
    ):
        """
        Lớp con triển khai việc vẽ biểu đồ.

        Args:
            axes:
                matplotlib Axes.

            data:
                dữ liệu đã được set_data().
        """
        raise NotImplementedError