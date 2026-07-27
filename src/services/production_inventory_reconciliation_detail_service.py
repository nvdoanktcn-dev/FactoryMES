from __future__ import annotations

from collections import defaultdict
from datetime import date

from src.models.import_detail import ImportDetail
from src.models.import_log import ImportLog


class ProductionInventoryReconciliationDetailService:
    """Build auditable detail for one Work Order and Product."""

    IMPORT_MODULE = "FINISHED_INVENTORY"

    def __init__(self, reconciliation_service):
        if reconciliation_service is None:
            raise ValueError(
                "Reconciliation service is required."
            )
        self.reconciliation_service = (
            reconciliation_service
        )

    def build_detail(
        self,
        start_date,
        end_date,
        *,
        work_order_no,
        product_code,
    ) -> dict:
        service = self.reconciliation_service
        work_order = service._code(work_order_no)
        product = service._code(product_code)

        if not work_order:
            raise ValueError("Work Order is required.")
        if not product:
            raise ValueError("Product Code is required.")

        report = service.build_report(
            start_date,
            end_date,
            work_order_no=work_order,
            product_code=product,
        )
        rows = list(report.get("rows", []) or [])

        if not rows:
            raise ValueError(
                "No reconciliation record was found for "
                f"{work_order} / {product}."
            )

        start = service._require_date(
            start_date,
            "Start Date",
        )
        end = service._require_date(
            end_date,
            "End Date",
        )
        production_logs = [
            record
            for record in (
                service.production_log_repository
                .get_by_date_range(start, end)
                or []
            )
            if service._production_key(record)
            == (work_order, product)
        ]
        inventory_records = [
            record
            for record in (
                service.finished_inventory_repository
                .get_all()
                or []
            )
            if (
                service._inventory_key(record)
                == (work_order, product)
                and service._date_in_range(
                    getattr(
                        record,
                        "inventory_date",
                        None,
                    ),
                    start,
                    end,
                )
            )
        ]
        production_orders = list(
            service.production_order_repository
            .get_all()
            or []
        )
        final_operations = service._final_operations(
            production_orders,
            production_logs,
        )
        final_logs = [
            record
            for record in production_logs
            if service._is_final_log(
                record,
                final_operations,
            )
        ]
        import_metadata = self._import_metadata(
            inventory_records
        )

        detail = dict(report)
        detail["selected_row"] = dict(rows[0])
        detail["daily_detail"] = self._daily_detail(
            production_logs,
            final_logs,
            inventory_records,
        )
        detail["production_detail"] = (
            self._production_detail(
                production_logs,
                final_operations,
            )
        )
        detail["inventory_receipts"] = (
            self._inventory_receipts(
                inventory_records,
                import_metadata,
            )
        )
        return detail

    def _daily_detail(
        self,
        production_logs,
        final_logs,
        inventory_records,
    ):
        grouped = defaultdict(
            lambda: {
                "final_op_qty": 0,
                "ng_qty": 0,
                "inventory_qty": 0,
            }
        )
        for record in final_logs:
            day = self._record_date(
                getattr(record, "start_time", None)
            )
            if day:
                grouped[day]["final_op_qty"] += (
                    self._integer(
                        getattr(record, "ok_qty", 0)
                    )
                )
        for record in production_logs:
            day = self._record_date(
                getattr(record, "start_time", None)
            )
            if day:
                grouped[day]["ng_qty"] += self._integer(
                    getattr(record, "ng_qty", 0)
                )
        for record in inventory_records:
            day = self._record_date(
                getattr(
                    record,
                    "inventory_date",
                    None,
                )
            )
            if day:
                grouped[day]["inventory_qty"] += (
                    self._integer(
                        getattr(record, "qty", 0)
                    )
                )

        rows = []
        cumulative_production = 0
        cumulative_inventory = 0
        for day in sorted(grouped):
            item = grouped[day]
            cumulative_production += (
                item["final_op_qty"]
            )
            cumulative_inventory += (
                item["inventory_qty"]
            )
            rows.append({
                "date": day,
                **item,
                "daily_variance": (
                    item["final_op_qty"]
                    - item["inventory_qty"]
                ),
                "cumulative_production":
                    cumulative_production,
                "cumulative_inventory":
                    cumulative_inventory,
                "cumulative_pending": max(
                    cumulative_production
                    - cumulative_inventory,
                    0,
                ),
                "cumulative_over": max(
                    cumulative_inventory
                    - cumulative_production,
                    0,
                ),
            })
        return rows

    def _production_detail(
        self,
        records,
        final_operations,
    ):
        service = self.reconciliation_service
        rows = []
        for record in sorted(
            records,
            key=lambda item: (
                str(
                    getattr(
                        item,
                        "start_time",
                        "",
                    )
                    or ""
                ),
                getattr(item, "id", 0) or 0,
            ),
        ):
            key = service._production_key(record)
            operation = service._operation_number(
                getattr(record, "op_no", 0)
            )
            rows.append({
                "production_log_id":
                    getattr(record, "id", None),
                "start_time":
                    getattr(record, "start_time", None),
                "finish_time":
                    getattr(record, "finish_time", None),
                "operation":
                    getattr(record, "op_no", ""),
                "is_final_operation": (
                    operation
                    == final_operations.get(key, 0)
                ),
                "machine_code":
                    getattr(record, "machine_code", ""),
                "employee_code":
                    getattr(record, "employee_code", ""),
                "shift":
                    getattr(record, "shift", ""),
                "ok_qty": self._integer(
                    getattr(record, "ok_qty", 0)
                ),
                "ng_qty": self._integer(
                    getattr(record, "ng_qty", 0)
                ),
                "run_time_hours": round(
                    self._number(
                        getattr(
                            record,
                            "run_time_sec",
                            0,
                        )
                    )
                    / 3600,
                    3,
                ),
                "downtime_min": round(
                    self._number(
                        getattr(
                            record,
                            "downtime_min",
                            0,
                        )
                    ),
                    2,
                ),
                "status":
                    getattr(record, "status", ""),
            })
        return rows

    def _inventory_receipts(
        self,
        records,
        metadata,
    ):
        rows = []
        for record in sorted(
            records,
            key=lambda item: (
                getattr(
                    item,
                    "inventory_date",
                    None,
                )
                or date.min,
                getattr(item, "inventory_id", 0)
                or 0,
            ),
        ):
            inventory_id = getattr(
                record,
                "inventory_id",
                None,
            )
            audit = metadata.get(
                int(inventory_id)
                if inventory_id is not None
                else -1,
                {},
            )
            rows.append({
                "inventory_id": inventory_id,
                "inventory_date": getattr(
                    record,
                    "inventory_date",
                    None,
                ),
                "qty": self._integer(
                    getattr(record, "qty", 0)
                ),
                "import_log_id": audit.get(
                    "import_log_id"
                ),
                "import_file": audit.get(
                    "import_file", ""
                ),
                "import_time": audit.get(
                    "import_time"
                ),
                "import_status": audit.get(
                    "import_status", "MANUAL"
                ),
            })
        return rows

    def _import_metadata(self, records):
        session = getattr(
            self.reconciliation_service,
            "session",
            None,
        )
        if session is None:
            return {}

        inventory_ids = [
            int(record.inventory_id)
            for record in records
            if getattr(
                record,
                "inventory_id",
                None,
            )
            is not None
        ]
        if not inventory_ids:
            return {}

        keys = [str(value) for value in inventory_ids]
        details = (
            session.query(ImportDetail)
            .filter(
                ImportDetail.module
                == self.IMPORT_MODULE,
                ImportDetail.action == "INSERT",
                ImportDetail.entity_key.in_(keys),
            )
            .order_by(ImportDetail.id.desc())
            .all()
        )
        log_ids = {
            int(detail.log_id)
            for detail in details
        }
        logs = (
            session.query(ImportLog)
            .filter(ImportLog.id.in_(log_ids))
            .all()
            if log_ids
            else []
        )
        logs_by_id = {
            int(log.id): log
            for log in logs
        }
        result = {}
        for detail in details:
            inventory_id = int(detail.entity_key)
            if inventory_id in result:
                continue
            log = logs_by_id.get(int(detail.log_id))
            if log is None:
                continue
            result[inventory_id] = {
                "import_log_id": log.id,
                "import_file": log.file_name or "",
                "import_time": log.import_time,
                "import_status": log.status or "",
            }
        return result

    @staticmethod
    def _record_date(value):
        if hasattr(value, "date"):
            return value.date()
        return value if isinstance(value, date) else None

    @staticmethod
    def _number(value):
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def _integer(cls, value):
        return int(round(cls._number(value)))
