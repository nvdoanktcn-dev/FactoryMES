from __future__ import annotations

from src.services.dashboard import (
    DashboardFacadeService,
    DashboardRequest,
)
from src.core.logging_config import (
    get_logger,
)

logger = get_logger(
    __name__
)


class DashboardController:
    """
    Dashboard Controller

    Chỉ điều phối giữa UI và DashboardFacadeService.

    Không chứa business logic.
    """

    def __init__(
        self,
        page,
        facade_service=None,
    ):
        self.page = page

        self.facade = (
            facade_service
            or DashboardFacadeService()
        )

        self.current_request = None

        self.last_response = None

    # ======================================================
    # Refresh
    # ======================================================
 
    def refresh(
        self,
        request,
    ):
        """
        Refresh Dashboard.
        """

        if isinstance(
            request,
            dict,
        ):
            request = DashboardRequest(
                **request
            )

        if not isinstance(
            request,
            DashboardRequest,
        ):
            raise TypeError(
                "DashboardController.refresh() "
                "requires DashboardRequest."
            )

        self.current_request = request

        logger.info(
            (
                "Dashboard refresh started: "
                "start=%s end=%s shift=%s "
                "machine=%s work_order=%s"
            ),
            request.start_date,
            request.end_date,
            request.shift,
            request.machine_code,
            request.work_order_no,
        )


        response = (
            self.facade.build(
                request
            )
        )
        logger.info(
            "Dashboard refresh completed."
        )
        
        self.last_response = response

        self.update_page()

        return response

    # ======================================================
    # Update UI
    # ======================================================

    def update_page(self):
        if self.last_response is None:
            return

        response = self.last_response

        if hasattr(
            self.page,
            "kpi_panel",
        ):
            self.page.kpi_panel.update_data(
                response.analytics
            )

        if hasattr(
            self.page,
            "chart_panel",
        ):
            self.page.chart_panel.update_data(
                response.charts
            )

        if hasattr(
            self.page,
            "table_panel",
        ):
            self.page.table_panel.update_data(
                {
                    "records":
                        response.records,

                    "import_history":
                        response.import_history,

                    "alarms":
                        response.alarms,
                }
            )

        if hasattr(
            self.page,
            "status_panel",
        ):
            self.page.status_panel.update_status(
                response.status
            )

    # ======================================================
    # Cache
    # ======================================================

    def invalidate_cache(self):
        self.facade.invalidate_cache()

    def cache_statistics(self):
        return (
            self.facade.cache_statistics()
        )

    # ======================================================
    # Refresh bypass cache
    # ======================================================

    def force_refresh(self):
        if self.current_request is None:
            return None

        response = (
            self.facade
            .build_without_cache(
                self.current_request
            )
        )

        self.last_response = response

        self.update_page()

        return response

    # ======================================================
    # Properties
    # ======================================================

    @property
    def response(self):
        return self.last_response

    @property
    def request(self):
        return self.current_request