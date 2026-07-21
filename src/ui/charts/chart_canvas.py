import six

# Workaround cho Shiboken + six._SixMetaPathImporter
if not hasattr(six._importer, "_path"):
    six._importer._path = six.__file__

from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg,
)

from matplotlib.figure import Figure

class ChartCanvas(FigureCanvasQTAgg):
    """
    Canvas matplotlib dùng trong PySide6.

    Chịu trách nhiệm:
    - Quản lý Figure.
    - Quản lý Axes.
    - Refresh biểu đồ.
    - Clear biểu đồ.
    """

    def __init__(
        self,
        parent=None,
        width=5,
        height=3.2,
        dpi=100,
    ):
        self.figure = Figure(
            figsize=(width, height),
            dpi=dpi,
            tight_layout=True,
        )

        super().__init__(self.figure)

        self.setParent(parent)

        self.axes = self.figure.add_subplot(
            111
        )

        self.setMinimumHeight(260)

    def clear(self):
        """
        Xóa toàn bộ nội dung biểu đồ.
        """
        self.axes.clear()
        self.draw_idle()

    def reset_axes(self):
        """
        Xóa Axes cũ và tạo Axes mới.
        """
        self.figure.clear()

        self.axes = self.figure.add_subplot(
            111
        )

        return self.axes

    def refresh(self):
        """
        Vẽ lại Canvas.
        """
        self.figure.tight_layout()
        self.draw_idle()

    def save_chart(
        self,
        file_path,
        dpi=150,
    ):
        """
        Lưu biểu đồ ra file PNG/JPG/PDF.
        """
        if not file_path:
            raise ValueError(
                "Chart file path is required."
            )

        self.figure.savefig(
            file_path,
            dpi=dpi,
            bbox_inches="tight",
        )