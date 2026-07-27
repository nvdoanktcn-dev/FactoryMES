from __future__ import annotations

from pathlib import Path

from src.services.manufacturing_analytics_service import (
    ManufacturingAnalyticsService,
)
from src.services.manufacturing_report_export_service import (
    ManufacturingReportExportService,
)
from src.services.detailed_manufacturing_report_export_service import (
    DetailedManufacturingReportExportService,
)


class ManufacturingReportService:
    """Application service for loading and exporting manufacturing reports."""

    def __init__(
        self,
        analytics_service=None,
        export_service=None,
        detailed_export_service=None,
    ) -> None:
        self._owns_analytics_service = (
            analytics_service is None
        )
        self.analytics_service = (
            analytics_service
            or ManufacturingAnalyticsService()
        )
        self.export_service = (
            export_service
            or ManufacturingReportExportService()
        )
        self.detailed_export_service = (
            detailed_export_service
            or DetailedManufacturingReportExportService()
        )

    def build_report(
        self,
        start_date,
        end_date,
        *,
        machine_group=None,
        machine_code=None,
        shift=None,
        work_order_no=None,
        product_code=None,
        employee_code=None,
    ):
        return self.analytics_service.build(
            start_date=start_date,
            end_date=end_date,
            machine_group=machine_group,
            machine_code=machine_code,
            shift=shift,
            work_order_no=work_order_no,
            product_code=product_code,
            employee_code=employee_code,
        )

    def export_report(
        self,
        report,
        output_path,
    ) -> Path:
        return self.export_service.export(
            report,
            output_path,
        )

    def export_report_bundle(
        self,
        report,
        output_path,
    ) -> tuple[Path, Path, Path]:
        """Export the standard report plus two detailed workbooks."""
        standard_path = self.export_report(
            report,
            output_path,
        )
        production_path, work_order_path = (
            self.detailed_export_service.export(
                report,
                standard_path.parent,
            )
        )
        return (
            standard_path,
            production_path,
            work_order_path,
        )

    def close(self) -> None:
        if not self._owns_analytics_service:
            return

        close_method = getattr(
            self.analytics_service,
            "close",
            None,
        )
        if callable(close_method):
            close_method()
