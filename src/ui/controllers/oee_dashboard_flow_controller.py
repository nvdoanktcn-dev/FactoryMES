from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal


class OEEDashboardFlowController(QObject):
    """
    Điều phối trạng thái tải và xuất dữ liệu của OEE Dashboard.

    Controller này không thay thế controller nghiệp vụ chịu trách nhiệm
    truy vấn và tổng hợp dữ liệu OEE.
    """

    loading_changed = Signal(bool)
    data_loaded = Signal(object)
    load_failed = Signal(str)

    export_started = Signal()
    export_completed = Signal(str)
    export_failed = Signal(str)

    def __init__(
        self,
        load_dashboard: Callable[[Any], Any],
        export_dashboard: Callable[[Any, str], Any],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._load_dashboard = load_dashboard
        self._export_dashboard = export_dashboard

        self.current_data: Any | None = None
        self.current_filters: Any | None = None
        self.last_error: str | None = None

    def refresh(
        self,
        filters: Any,
    ) -> Any | None:
        if self.current_data is not None:
            # Dữ liệu cũ vẫn được giữ cho đến khi lần tải mới hoàn tất.
            pass

        self.loading_changed.emit(True)
        self.last_error = None
        self.current_filters = filters

        try:
            data = self._load_dashboard(filters)

            self.current_data = data
            self.data_loaded.emit(data)

            return data

        except Exception as exc:
            self.current_data = None
            self.last_error = str(exc)

            self.load_failed.emit(
                self.last_error
            )
            return None

        finally:
            self.loading_changed.emit(False)

    def export_excel(
        self,
        file_path: str | Path,
    ) -> bool:
        if self.current_data is None:
            self.export_failed.emit(
                "Không có dữ liệu Dashboard để export."
            )
            return False

        normalized_path = str(
            Path(file_path)
        )

        self.export_started.emit()

        try:
            self._export_dashboard(
                self.current_data,
                normalized_path,
            )

            self.export_completed.emit(
                normalized_path
            )
            return True

        except Exception as exc:
            self.last_error = str(exc)

            self.export_failed.emit(
                self.last_error
            )
            return False

    def clear(self) -> None:
        self.current_data = None
        self.current_filters = None
        self.last_error = None

    @property
    def has_data(self) -> bool:
        return self.current_data is not None