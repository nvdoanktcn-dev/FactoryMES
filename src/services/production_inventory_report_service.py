from __future__ import annotations

from pathlib import Path

from src.services.production_inventory_reconciliation_detail_export_service import (
    ProductionInventoryReconciliationDetailExportService,
)
from src.services.production_inventory_reconciliation_detail_service import (
    ProductionInventoryReconciliationDetailService,
)
from src.services.production_inventory_reconciliation_export_service import (
    ProductionInventoryReconciliationExportService,
)
from src.services.production_inventory_reconciliation_service import (
    ProductionInventoryReconciliationService,
)


class ProductionInventoryReportService:
    """Application facade for production/inventory reconciliation."""

    def __init__(
        self,
        reconciliation_service=None,
        export_service=None,
        detail_service=None,
        detail_export_service=None,
    ) -> None:
        self._owns_reconciliation_service = (
            reconciliation_service is None
        )
        self.reconciliation_service = (
            reconciliation_service
            or ProductionInventoryReconciliationService()
        )
        self.export_service = (
            export_service
            or ProductionInventoryReconciliationExportService()
        )
        self.detail_service = (
            detail_service
            or ProductionInventoryReconciliationDetailService(
                self.reconciliation_service
            )
        )
        self.detail_export_service = (
            detail_export_service
            or ProductionInventoryReconciliationDetailExportService()
        )

    def build_report(
        self,
        start_date,
        end_date,
        *,
        work_order_no=None,
        product_code=None,
        status=None,
    ):
        return self.reconciliation_service.build_report(
            start_date,
            end_date,
            work_order_no=work_order_no,
            product_code=product_code,
            status=status,
        )

    def build_detail(
        self,
        start_date,
        end_date,
        *,
        work_order_no,
        product_code,
    ):
        return self.detail_service.build_detail(
            start_date,
            end_date,
            work_order_no=work_order_no,
            product_code=product_code,
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

    def export_detail(
        self,
        detail,
        output_path,
    ) -> Path:
        return self.detail_export_service.export(
            detail,
            output_path,
        )

    def close(self) -> None:
        if not self._owns_reconciliation_service:
            return
        self.reconciliation_service.close()
