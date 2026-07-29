from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from src.services.base_service import SessionOwnedService

from src.services.dashboard.dashboard_cache import (
    DashboardCache,
)

from src.services.dashboard.dashboard_request import (
    DashboardRequest,
)

from src.services.dashboard.dashboard_response import (
    DashboardResponse,
)

from src.services.dashboard_chart_service import (
    DashboardChartService,
)

from src.services.manufacturing_analytics_service import (
    ManufacturingAnalyticsService,
)

from src.services.system_status_service import (
    SystemStatusService,
)

from src.services.alarm_service import (
    AlarmService,
)
from src.core.logging_config import (
    get_logger,
)

logger = get_logger(
    __name__
)

class DashboardFacadeService(SessionOwnedService):
    """
    Dashboard Facade Service

    DashboardController chỉ giao tiếp với class này.

    Trách nhiệm:

    - Validate request
    - Quản lý cache
    - Điều phối Analytics
    - Điều phối Charts
    - Điều phối Status
    - Trả DashboardResponse

    Không truy cập UI.

    Không truy cập Repository trực tiếp.
    """

    DEFAULT_CACHE_SECONDS = 60

    def __init__(
        self,
        session: Session | None = None,
        analytics_service: Optional[
            ManufacturingAnalyticsService
        ] = None,
        chart_service: Optional[
            DashboardChartService
        ] = None,
        status_service: Optional[
            SystemStatusService
        ] = None,
        alarm_service: Optional[
            AlarmService
        ] = None,
        cache: Optional[
            DashboardCache
        ] = None,
    ):
        super().__init__(session=session)

        self.analytics_service = (
            analytics_service
            or ManufacturingAnalyticsService(
                session=self.require_session()
            )
        )

        self.chart_service = (
            chart_service
            or DashboardChartService()
        )

        self.status_service = (
            status_service
            or SystemStatusService()
        )

        # Giai đoạn 7 (MES Real-time, 2026-07-28): trước đây
        # `alarms` luôn là [] vì không có nguồn dữ liệu thật nào
        # đứng sau (xem `_section(analytics, "alarms", [])` bên
        # dưới, phần "analytics" chưa từng có khoá "alarms"). Alarm
        # là một khái niệm KHÔNG phụ thuộc filter ngày/máy/ca của
        # Dashboard - nên lấy trực tiếp từ AlarmService thay vì đi
        # qua ManufacturingAnalyticsService, xem `_build_alarms()`.
        self.alarm_service = (
            alarm_service
            or AlarmService(
                session=self.require_session()
            )
        )

        self.cache = (
            cache
            or DashboardCache(
                ttl_seconds=self.DEFAULT_CACHE_SECONDS
            )
        )

    def close(self) -> None:
        """
        Đóng các dependency do Facade sở hữu và cuối cùng
        đóng session nếu Facade là nơi đã tạo session.
        """
        analytics_close = getattr(
            self.analytics_service,
            "close",
            None,
        )

        if callable(analytics_close):
            analytics_close()

        status_close = getattr(
            self.status_service,
            "close",
            None,
        )

        if callable(status_close):
            status_close()

        alarm_close = getattr(
            self.alarm_service,
            "close",
            None,
        )

        if callable(alarm_close):
            alarm_close()

        super().close()

    # ==========================================================
    # Public API
    # ==========================================================

    def build(
        self,
        request: DashboardRequest,
    ) -> DashboardResponse:
        """
        Build Dashboard.

        Quy trình:

            Validate

                ↓

            Cache

                ↓

            Analytics

                ↓

            Charts

                ↓

            Status

                ↓

            DashboardResponse
        """

        self._validate_request(
            request
        )

        cache_key = self._cache_key(
            request
        )

        cached = self.cache.get(
            cache_key
        )

        if cached is not None:
            return cached

        analytics = (
            self._build_analytics(
                request
            )
        )

        charts = (
            self._build_charts(
                analytics
            )
        )

        status = (
            self._build_status()
        )

        response = DashboardResponse(
            analytics=analytics,

            charts=charts,

            status=status,

            records=self._section(
                analytics,
                "records",
                [],
            ),

            import_history=self._section(
                analytics,
                "import_history",
                [],
            ),

            alarms=self._build_alarms(),
        )

        self.cache.put(
            cache_key,
            response,
        )

        return response

            # ==========================================================
    # Build sections
    # ==========================================================

    def _build_analytics(
        self,
        request: DashboardRequest,
    ):
        """
        Gọi ManufacturingAnalyticsService.

        Kết quả chuẩn phải là dictionary.
        """

        analytics = (
            self.analytics_service.build(
                start_date=request.start_date,
                end_date=request.end_date,
                shift=self._optional_code(
                    request.shift
                ),
                machine_code=self._optional_code(
                    request.machine_code
                ),
                employee_code=self._optional_code(
                    request.employee_code
                ),
                product_code=self._optional_code(
                    request.product_code
                ),
                work_order_no=self._optional_code(
                    request.work_order_no
                ),
            )
        )

        if analytics is None:
            return {}

        if not isinstance(
            analytics,
            dict,
        ):
            raise TypeError(
                "ManufacturingAnalyticsService.build() "
                "must return a dictionary."
            )

        return analytics

    def _build_charts(
        self,
        analytics,
    ):
        """
        Chuyển Analytics thành ChartData.
        """

        charts = self.chart_service.build(
            analytics
        )

        if charts is None:
            return {}

        if not isinstance(
            charts,
            dict,
        ):
            raise TypeError(
                "DashboardChartService.build() "
                "must return a dictionary."
            )

        return charts

    def _build_alarms(self):
        """
        Lấy Alarm thật (OPEN/ACKNOWLEDGED, mới nhất trước) cho bảng
        AlarmTable trên Dashboard và sheet "Alarms" khi export. Nếu
        AlarmService lỗi vì bất kỳ lý do gì, Dashboard vẫn phải build
        được bình thường (giống `_build_status()`) - chỉ phần Alarm
        trống, không làm sập toàn bộ Dashboard.
        """

        try:
            alarms = (
                self.alarm_service.get_open_alarms(
                    limit=100
                )
            )
        except Exception as error:  # noqa: BLE001
            logger.warning(
                "Could not load Alarms for Dashboard: "
                f"{error}"
            )
            return []

        return [
            {
                "time": alarm.raised_at,
                "level": alarm.severity,
                "module": alarm.machine_code,
                "code": alarm.alarm_code,
                "message": alarm.message,
                "status": alarm.status,
            }
            for alarm in alarms
        ]

    def _build_status(self):
        """
        Lấy trạng thái hệ thống.

        Nếu việc đọc trạng thái thất bại,
        Dashboard vẫn được trả về với status ERROR.
        """

        try:
            status = (
                self.status_service
                .build_status()
            )

            if status is None:
                return self._default_status(
                    dashboard_status="WARNING",
                    dashboard_message=(
                        "SystemStatusService returned "
                        "no status data."
                    ),
                )

            if not isinstance(
                status,
                dict,
            ):
                raise TypeError(
                    "SystemStatusService.build_status() "
                    "must return a dictionary."
                )

            return status

        except Exception as error:
            return self._default_status(
                database_status="UNKNOWN",
                database_message=(
                    "Database status could not "
                    "be determined."
                ),
                dashboard_status="ERROR",
                dashboard_message=str(error),
            )

    # ==========================================================
    # Request validation
    # ==========================================================

    @classmethod
    def _validate_request(
        cls,
        request,
    ):
        if request is None:
            raise ValueError(
                "DashboardRequest is required."
            )

        if not isinstance(
            request,
            DashboardRequest,
        ):
            raise TypeError(
                "DashboardFacadeService.build() "
                "requires DashboardRequest."
            )

        if request.start_date is None:
            raise ValueError(
                "Dashboard Start Date is required."
            )

        if request.end_date is None:
            raise ValueError(
                "Dashboard End Date is required."
            )

        if (
            request.end_date
            < request.start_date
        ):
            raise ValueError(
                "Dashboard End Date cannot be "
                "earlier than Start Date."
            )

        cls._validate_optional_code(
            field_name="Shift",
            value=request.shift,
        )

        cls._validate_optional_code(
            field_name="Machine Code",
            value=request.machine_code,
        )

        cls._validate_optional_code(
            field_name="Employee Code",
            value=request.employee_code,
        )

        cls._validate_optional_code(
            field_name="Product Code",
            value=request.product_code,
        )

        cls._validate_optional_code(
            field_name="Work Order No",
            value=request.work_order_no,
        )

        refresh_interval = cls._to_int(
            request.refresh_interval,
            default=60,
        )

        if refresh_interval <= 0:
            raise ValueError(
                "Refresh Interval must be greater "
                "than zero."
            )

        return True

    @staticmethod
    def _validate_optional_code(
        field_name,
        value,
    ):
        if value is None:
            return

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be a string "
                "or None."
            )

    # ==========================================================
    # Cache key
    # ==========================================================

    @classmethod
    def _cache_key(
        cls,
        request: DashboardRequest,
    ):
        """
        Cache key chỉ gồm các filter ảnh hưởng dữ liệu.

        auto_refresh và refresh_interval không làm
        thay đổi nội dung Analytics nên không đưa
        vào cache key.
        """

        return (
            request.start_date,
            request.end_date,
            cls._optional_code(
                request.shift
            ),
            cls._optional_code(
                request.machine_code
            ),
            cls._optional_code(
                request.employee_code
            ),
            cls._optional_code(
                request.product_code
            ),
            cls._optional_code(
                request.work_order_no
            ),
        )

    # ==========================================================
    # Cache API
    # ==========================================================

    def invalidate_cache(
        self,
        request: Optional[
            DashboardRequest
        ] = None,
    ):
        """
        Xóa cache.

        request=None:
            Xóa toàn bộ Dashboard cache.

        request được cung cấp:
            Chỉ xóa cache của filter tương ứng.
        """

        if request is None:
            self.cache.invalidate()
            return

        self._validate_request(
            request
        )

        self.cache.invalidate(
            self._cache_key(request)
        )

    def cache_statistics(self):
        """
        Trả thông tin cache hiện tại.
        """

        return self.cache.statistics()

    def build_without_cache(
        self,
        request: DashboardRequest,
    ) -> DashboardResponse:
        """
        Build mới hoàn toàn, bỏ qua cache.

        Dùng khi:
        - Người dùng vừa Import.
        - Vừa ghi Production Log.
        - Work Order vừa thay đổi.
        - Cần Refresh dữ liệu mới ngay lập tức.
        """

        self._validate_request(
            request
        )

        cache_key = self._cache_key(
            request
        )

        self.cache.invalidate(
            cache_key
        )

        return self.build(
            request
        )

    # ==========================================================
    # Default status
    # ==========================================================

    @staticmethod
    def _default_status(
        database_status="UNKNOWN",
        database_message=(
            "Database status is unknown."
        ),
        dashboard_status="ONLINE",
        dashboard_message=(
            "Dashboard data was built."
        ),
    ):
        return {
            "database": {
                "status":
                    database_status,

                "message":
                    database_message,
            },

            "analytics": {
                "status":
                    "ONLINE",

                "message":
                    "Analytics build completed.",
            },

            "dashboard": {
                "status":
                    dashboard_status,

                "message":
                    dashboard_message,
            },

            "plc": {
                "status":
                    "NOT_CONFIGURED",

                "message":
                    (
                        "PLC / OPC-UA is not "
                        "configured."
                    ),
            },

            "last_check":
                None,

            "current_shift":
                "-",

            "version":
                "-",
        }

    # ==========================================================
    # Data helpers
    # ==========================================================

    @staticmethod
    def _section(
        source,
        key,
        default,
    ):
        if source is None:
            return default

        if isinstance(
            source,
            dict,
        ):
            value = source.get(
                key,
                default,
            )

        else:
            value = getattr(
                source,
                key,
                default,
            )

        if value is None:
            return default

        return value

    @staticmethod
    def _optional_code(value):
        """
        Chuẩn hóa filter code.

        Chuỗi rỗng được chuyển thành None để
        Service hiểu là không lọc.
        """

        if value is None:
            return None

        normalized = str(
            value
        ).strip().upper()

        return normalized or None

    @staticmethod
    def _to_int(
        value,
        default=0,
    ):
        try:
            return int(
                float(value)
            )

        except (
            TypeError,
            ValueError,
        ):
            return int(default)