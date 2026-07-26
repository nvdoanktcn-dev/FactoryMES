from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from PySide6.QtCore import QObject, QTimer, Signal


class DashboardCoordinatorProtocol(Protocol):
    @property
    def current_data(self) -> Any | None:
        ...

    @property
    def current_filters(self) -> Any | None:
        ...

    @property
    def has_data(self) -> bool:
        ...

    @property
    def version(self) -> int:
        ...

    def load(self, filters: Any) -> Any:
        ...

    def refresh(self, filters: Any) -> Any:
        ...

    def invalidate(self) -> None:
        ...


class OEEDashboardFlowController(QObject):
    """
    Điều phối trạng thái tải, xuất dữ liệu và tự động làm mới
    của OEE Dashboard.

    Controller này không chứa logic nghiệp vụ OEE.
    """

    DEFAULT_REFRESH_INTERVAL_MS = 60_000
    MIN_REFRESH_INTERVAL_MS = 1_000

    loading_changed = Signal(bool)
    data_loaded = Signal(object)
    load_failed = Signal(str)

    export_started = Signal()
    export_completed = Signal(str)
    export_failed = Signal(str)

    auto_refresh_started = Signal(int)
    auto_refresh_stopped = Signal()
    auto_refresh_triggered = Signal()
    refresh_interval_changed = Signal(int)

    def __init__(
        self,
        load_dashboard: Callable[[Any], Any] | None = None,
        export_dashboard: Callable[[Any, str], Any] | None = None,
        parent: QObject | None = None,
        *,
        coordinator: DashboardCoordinatorProtocol | None = None,
    ) -> None:
        super().__init__(parent)

        if coordinator is None and not callable(load_dashboard):
            raise TypeError(
                "load_dashboard must be callable when "
                "coordinator is not provided."
            )

        if coordinator is not None:
            self._validate_coordinator(coordinator)

        if not callable(export_dashboard):
            raise TypeError(
                "export_dashboard must be callable."
            )

        self._coordinator = coordinator
        self._load_dashboard = load_dashboard
        self._export_dashboard = export_dashboard

        self.current_data: Any | None = None
        self.current_filters: Any | None = None
        self.last_error: str | None = None

        self._loading = False

        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.setSingleShot(False)
        self._auto_refresh_timer.setInterval(
            self.DEFAULT_REFRESH_INTERVAL_MS
        )
        self._auto_refresh_timer.timeout.connect(
            self._on_auto_refresh_timeout
        )

    @property
    def coordinator(
        self,
    ) -> DashboardCoordinatorProtocol | None:
        return self._coordinator


    @property
    def uses_coordinator(self) -> bool:
        return self._coordinator is not None


    @property
    def data_version(self) -> int:
        if self._coordinator is None:
            return 0

        return self._coordinator.version

   
    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def refresh(
        self,
        filters: Any,
        *,
        force: bool = True,
    ) -> Any | None:
        """
        Tải dữ liệu Dashboard.

        force=True:
            Luôn tải mới. Phù hợp với nút Refresh và Auto Refresh.

        force=False:
            Cho phép Coordinator dùng dữ liệu cache nếu filter không đổi.

        Khi chưa tích hợp Coordinator, controller vẫn sử dụng callable cũ.
        """

        if self._loading:
            return None

        self._loading = True
        self.loading_changed.emit(True)

        self.last_error = None
        self.current_filters = filters

        try:
            data = self._load_data(
                filters,
                force=force,
            )

            self.current_data = data
            self.data_loaded.emit(data)

            return data

        except Exception as exc:
            # Không xóa dữ liệu cũ khi refresh thất bại.
            # Cache/Coordinator cũng giữ snapshot thành công gần nhất.
            self.last_error = str(exc)

            self.load_failed.emit(
                self.last_error
            )

            return None

        finally:
            self._loading = False
            self.loading_changed.emit(False)

    def refresh_once(self) -> Any | None:
        """
        Làm mới Dashboard bằng bộ lọc gần nhất.

        Hàm này được dùng cho Auto Refresh và có thể được gọi trực tiếp
        từ UI.
        """

        if self.current_filters is None:
            self.last_error = (
                "Chưa có bộ lọc Dashboard để làm mới."
            )

            self.load_failed.emit(
                self.last_error
            )

            return None

        return self.refresh(
            self.current_filters
        )

    # ------------------------------------------------------------------
    # Auto refresh
    # ------------------------------------------------------------------

    def start_auto_refresh(
        self,
        interval_ms: int | None = None,
        *,
        refresh_immediately: bool = False,
    ) -> None:
        """
        Bật tự động làm mới Dashboard.

        Args:
            interval_ms:
                Chu kỳ làm mới tính bằng milliseconds.
                Nếu None thì giữ interval hiện tại.
            refresh_immediately:
                Nếu True, gọi refresh_once() ngay trước khi timer bắt đầu.
        """

        if interval_ms is not None:
            self.set_refresh_interval(
                interval_ms
            )

        if refresh_immediately:
            self.refresh_once()

        if self._auto_refresh_timer.isActive():
            return

        self._auto_refresh_timer.start()

        self.auto_refresh_started.emit(
            self.refresh_interval_ms
        )

    def stop_auto_refresh(self) -> None:
        """
        Dừng tự động làm mới Dashboard.
        """

        if not self._auto_refresh_timer.isActive():
            return

        self._auto_refresh_timer.stop()
        self.auto_refresh_stopped.emit()

    def set_refresh_interval(
        self,
        interval_ms: int,
    ) -> None:
        """
        Thay đổi chu kỳ Auto Refresh.
        """

        if isinstance(interval_ms, bool):
            raise TypeError(
                "interval_ms must be an integer."
            )

        try:
            normalized = int(interval_ms)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise TypeError(
                "interval_ms must be an integer."
            ) from exc

        if normalized < self.MIN_REFRESH_INTERVAL_MS:
            raise ValueError(
                "interval_ms must be at least "
                f"{self.MIN_REFRESH_INTERVAL_MS}."
            )

        if normalized == self.refresh_interval_ms:
            return

        was_active = (
            self._auto_refresh_timer.isActive()
        )

        self._auto_refresh_timer.setInterval(
            normalized
        )

        if was_active:
            self._auto_refresh_timer.start()

        self.refresh_interval_changed.emit(
            normalized
        )
    
    def load(
        self,
        filters: Any,
    ) -> Any | None:
        """
        Tải Dashboard và cho phép sử dụng cache.

        Dùng cho lần mở trang hoặc áp dụng lại cùng một bộ lọc.
        """

        return self.refresh(
            filters,
            force=False,
        )


    def _load_data(
        self,
        filters: Any,
        *,
        force: bool,
    ) -> Any:
        if self._coordinator is not None:
            if force:
                return self._coordinator.refresh(
                    filters
                )

            return self._coordinator.load(
                filters
            )

        if self._load_dashboard is None:
            raise RuntimeError(
                "Dashboard data loader is not configured."
            )

        return self._load_dashboard(filters)


    def is_auto_refresh_enabled(self) -> bool:
        return self._auto_refresh_timer.isActive()

    @property
    def refresh_interval_ms(self) -> int:
        return self._auto_refresh_timer.interval()

    @property
    def is_loading(self) -> bool:
        return self._loading

    def _on_auto_refresh_timeout(self) -> None:
        """
        Slot nội bộ của QTimer.
        """

        if self._loading:
            return

        if self.current_filters is None:
            return

        self.auto_refresh_triggered.emit()
        self.refresh_once()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

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
            result = self._export_dashboard(
                self.current_data,
                normalized_path,
            )

            self.export_completed.emit(
                str(result or normalized_path)
            )

            return True

        except Exception as exc:
            self.last_error = str(exc)

            self.export_failed.emit(
                self.last_error
            )

            return False

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def clear(self) -> None:
        self.stop_auto_refresh()

        if self._coordinator is not None:
            self._coordinator.invalidate()

        self.current_data = None
        self.current_filters = None
        self.last_error = None
        self._loading = False

    @property
    def has_data(self) -> bool:
        if self._coordinator is not None:
            return self._coordinator.has_data

        return self.current_data is not None

    @staticmethod
    def _validate_coordinator(
        coordinator: DashboardCoordinatorProtocol,
    ) -> None:
        required_members = (
            "current_data",
            "current_filters",
            "has_data",
            "version",
            "load",
            "refresh",
            "invalidate",
        )

        for member_name in required_members:
            if not hasattr(
                coordinator,
                member_name,
            ):
                raise TypeError(
                "coordinator must provide "
                    f"{member_name}."
                )

        for method_name in (
            "load",
            "refresh",
            "invalidate",
        ):
            if not callable(
                getattr(
                    coordinator,
                    method_name,
                )
            ):
                raise TypeError(
                    "coordinator."
                    f"{method_name} must be callable."
                )
