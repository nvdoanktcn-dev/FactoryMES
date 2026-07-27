from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from math import isfinite

from src.database.session import get_session
from src.repository.finished_inventory_repository import (
    FinishedInventoryRepository,
)
from src.repository.production_log_repository import (
    ProductionLogRepository,
)
from src.repository.production_order_repository import (
    ProductionOrderRepository,
)
from src.repository.work_order_repository import (
    WorkOrderRepository,
)


class ProductionInventoryReconciliationService:
    """Reconcile final-operation production with finished inventory."""

    STATUS_RECONCILED = "RECONCILED"
    STATUS_PENDING = "PENDING_INVENTORY"
    STATUS_OVER = "OVER_RECEIVED"
    STATUS_BEHIND = "BEHIND_PLAN"

    def __init__(
        self,
        session=None,
        *,
        work_order_repository=None,
        production_order_repository=None,
        production_log_repository=None,
        finished_inventory_repository=None,
    ) -> None:
        repositories = (
            work_order_repository,
            production_order_repository,
            production_log_repository,
            finished_inventory_repository,
        )
        all_injected = all(
            repository is not None
            for repository in repositories
        )
        self._owns_session = (
            session is None
            and not all_injected
        )
        self.session = (
            session
            or (
                None
                if all_injected
                else get_session()
            )
        )
        self.work_order_repository = (
            work_order_repository
            or WorkOrderRepository(self.session)
        )
        self.production_order_repository = (
            production_order_repository
            or ProductionOrderRepository(
                self.session
            )
        )
        self.production_log_repository = (
            production_log_repository
            or ProductionLogRepository(
                self.session
            )
        )
        self.finished_inventory_repository = (
            finished_inventory_repository
            or FinishedInventoryRepository(
                self.session
            )
        )

    def build_report(
        self,
        start_date,
        end_date,
        *,
        work_order_no=None,
        product_code=None,
        status=None,
    ) -> dict:
        start = self._require_date(
            start_date,
            "Start Date",
        )
        end = self._require_date(
            end_date,
            "End Date",
        )
        if end < start:
            raise ValueError(
                "End Date cannot be earlier than Start Date."
            )

        work_order_filter = self._code(
            work_order_no
        )
        product_filter = self._code(
            product_code
        )
        status_filter = self._code(status)

        work_orders = list(
            self.work_order_repository.get_all()
            or []
        )
        production_orders = list(
            self.production_order_repository.get_all()
            or []
        )
        production_logs = list(
            self.production_log_repository
            .get_by_date_range(start, end)
            or []
        )
        inventory_records = [
            record
            for record in (
                self.finished_inventory_repository
                .get_all()
                or []
            )
            if self._date_in_range(
                getattr(
                    record,
                    "inventory_date",
                    None,
                ),
                start,
                end,
            )
        ]

        final_operations = (
            self._final_operations(
                production_orders,
                production_logs,
            )
        )
        final_logs = [
            record
            for record in production_logs
            if self._is_final_log(
                record,
                final_operations,
            )
        ]

        rows = self._build_rows(
            start=start,
            end=end,
            work_orders=work_orders,
            production_logs=production_logs,
            final_logs=final_logs,
            inventory_records=inventory_records,
        )
        rows = [
            row
            for row in rows
            if (
                not work_order_filter
                or row["work_order_no"]
                == work_order_filter
            )
            and (
                not product_filter
                or row["product_code"]
                == product_filter
            )
            and (
                not status_filter
                or row["reconciliation_status"]
                == status_filter
            )
        ]
        selected_keys = {
            (
                row["work_order_no"],
                row["product_code"],
            )
            for row in rows
        }
        selected_final_logs = [
            record
            for record in final_logs
            if self._production_key(record)
            in selected_keys
        ]
        selected_inventory_records = [
            record
            for record in inventory_records
            if self._inventory_key(record)
            in selected_keys
        ]

        return {
            "period": {
                "start_date": start,
                "end_date": end,
                "day_count": (
                    end - start
                ).days + 1,
            },
            "filters": {
                "work_order_no":
                    work_order_filter,
                "product_code":
                    product_filter,
                "status":
                    status_filter,
            },
            "summary": self._summary(rows),
            "rows": rows,
            "daily": self._daily_rows(
                selected_final_logs,
                selected_inventory_records,
            ),
            "inventory_detail": (
                self._inventory_detail(
                    selected_inventory_records
                )
            ),
            "record_count": len(rows),
        }

    def _build_rows(
        self,
        *,
        start,
        end,
        work_orders,
        production_logs,
        final_logs,
        inventory_records,
    ) -> list[dict]:
        orders_by_key = {
            (
                self._code(
                    getattr(
                        order,
                        "work_order_no",
                        "",
                    )
                ),
                self._code(
                    getattr(
                        order,
                        "product_code",
                        "",
                    )
                ),
            ): order
            for order in work_orders
        }
        keys = set()
        for order in work_orders:
            if self._work_order_overlaps(
                order,
                start,
                end,
            ):
                keys.add(
                    self._work_order_key(order)
                )
        for record in production_logs:
            keys.add(self._production_key(record))
        for record in inventory_records:
            keys.add(self._inventory_key(record))

        final_by_key = defaultdict(list)
        all_logs_by_key = defaultdict(list)
        inventory_by_key = defaultdict(list)
        for record in final_logs:
            final_by_key[
                self._production_key(record)
            ].append(record)
        for record in production_logs:
            all_logs_by_key[
                self._production_key(record)
            ].append(record)
        for record in inventory_records:
            inventory_by_key[
                self._inventory_key(record)
            ].append(record)

        rows = []
        for key in sorted(keys):
            work_order_no, product_code = key
            order = orders_by_key.get(key)
            completed_records = final_by_key[key]
            all_records = all_logs_by_key[key]
            inventory = inventory_by_key[key]

            plan_qty = self._integer(
                getattr(order, "plan_qty", 0)
                if order is not None
                else 0
            )
            completed_qty = sum(
                self._integer(
                    getattr(
                        record,
                        "ok_qty",
                        0,
                    )
                )
                for record in completed_records
            )
            ng_qty = sum(
                self._integer(
                    getattr(
                        record,
                        "ng_qty",
                        0,
                    )
                )
                for record in all_records
            )
            inventory_qty = sum(
                self._integer(
                    getattr(record, "qty", 0)
                )
                for record in inventory
            )
            pending_qty = max(
                completed_qty - inventory_qty,
                0,
            )
            over_qty = max(
                inventory_qty - completed_qty,
                0,
            )
            remaining_plan_qty = max(
                plan_qty - completed_qty,
                0,
            )
            rows.append({
                "work_order_no": work_order_no,
                "product_code": product_code,
                "plan_qty": plan_qty,
                "completed_qty": completed_qty,
                "ng_qty": ng_qty,
                "inventory_qty": inventory_qty,
                "pending_inventory_qty":
                    pending_qty,
                "over_received_qty": over_qty,
                "remaining_plan_qty":
                    remaining_plan_qty,
                "completion_percent":
                    self._percentage(
                        completed_qty,
                        plan_qty,
                    ),
                "inventory_percent":
                    self._percentage(
                        inventory_qty,
                        completed_qty,
                    ),
                "work_order_status": self._code(
                    getattr(
                        order,
                        "status",
                        "",
                    )
                    if order is not None
                    else ""
                ),
                "reconciliation_status":
                    self._reconciliation_status(
                        plan_qty=plan_qty,
                        completed_qty=completed_qty,
                        inventory_qty=inventory_qty,
                    ),
                "last_production_date":
                    self._latest_date(
                        completed_records,
                        "start_time",
                    ),
                "last_inventory_date":
                    self._latest_date(
                        inventory,
                        "inventory_date",
                    ),
            })
        return rows

    def _final_operations(
        self,
        production_orders,
        production_logs,
    ) -> dict[tuple[str, str], int]:
        result = {}
        for order in production_orders:
            if self._code(
                getattr(order, "status", "")
            ) == "CANCELLED":
                continue
            key = self._production_key(order)
            operation = self._operation_number(
                getattr(
                    order,
                    "operation_no",
                    0,
                )
            )
            result[key] = max(
                result.get(key, 0),
                operation,
            )
        for record in production_logs:
            key = self._production_key(record)
            if key not in result:
                operation = self._operation_number(
                    getattr(record, "op_no", 0)
                )
                result[key] = max(
                    result.get(key, 0),
                    operation,
                )
        return result

    def _is_final_log(
        self,
        record,
        final_operations,
    ) -> bool:
        if self._code(
            getattr(record, "status", "")
        ) == "CANCELLED":
            return False
        key = self._production_key(record)
        return (
            self._operation_number(
                getattr(record, "op_no", 0)
            )
            == final_operations.get(key, 0)
        )

    def _daily_rows(
        self,
        final_logs,
        inventory_records,
    ) -> list[dict]:
        grouped = defaultdict(
            lambda: {
                "completed_qty": 0,
                "inventory_qty": 0,
            }
        )
        for record in final_logs:
            production_date = self._to_date(
                getattr(
                    record,
                    "start_time",
                    None,
                )
            )
            if production_date:
                grouped[production_date][
                    "completed_qty"
                ] += self._integer(
                    getattr(record, "ok_qty", 0)
                )
        for record in inventory_records:
            inventory_date = self._to_date(
                getattr(
                    record,
                    "inventory_date",
                    None,
                )
            )
            if inventory_date:
                grouped[inventory_date][
                    "inventory_qty"
                ] += self._integer(
                    getattr(record, "qty", 0)
                )
        output = []
        for production_date in sorted(grouped):
            item = grouped[production_date]
            completed = item["completed_qty"]
            inventory = item["inventory_qty"]
            output.append({
                "production_date":
                    production_date,
                "completed_qty": completed,
                "inventory_qty": inventory,
                "pending_inventory_qty":
                    max(
                        completed - inventory,
                        0,
                    ),
                "over_received_qty":
                    max(
                        inventory - completed,
                        0,
                    ),
            })
        return output

    def _inventory_detail(
        self,
        records,
    ) -> list[dict]:
        return sorted(
            [
                {
                    "inventory_date":
                        self._to_date(
                            getattr(
                                record,
                                "inventory_date",
                                None,
                            )
                        ),
                    "work_order_no":
                        self._code(
                            getattr(
                                record,
                                "work_order",
                                "",
                            )
                        ),
                    "product_code":
                        self._code(
                            getattr(
                                record,
                                "product_code",
                                "",
                            )
                        ),
                    "qty": self._integer(
                        getattr(record, "qty", 0)
                    ),
                }
                for record in records
            ],
            key=lambda row: (
                row["inventory_date"]
                or date.min,
                row["work_order_no"],
                row["product_code"],
            ),
        )

    @classmethod
    def _summary(cls, rows) -> dict:
        plan_qty = sum(
            row["plan_qty"]
            for row in rows
        )
        completed_qty = sum(
            row["completed_qty"]
            for row in rows
        )
        inventory_qty = sum(
            row["inventory_qty"]
            for row in rows
        )
        return {
            "work_order_count": len(rows),
            "plan_qty": plan_qty,
            "completed_qty": completed_qty,
            "ng_qty": sum(
                row["ng_qty"]
                for row in rows
            ),
            "inventory_qty": inventory_qty,
            "pending_inventory_qty": sum(
                row["pending_inventory_qty"]
                for row in rows
            ),
            "over_received_qty": sum(
                row["over_received_qty"]
                for row in rows
            ),
            "remaining_plan_qty": sum(
                row["remaining_plan_qty"]
                for row in rows
            ),
            "completion_percent":
                cls._percentage(
                    completed_qty,
                    plan_qty,
                ),
            "inventory_percent":
                cls._percentage(
                    inventory_qty,
                    completed_qty,
                ),
            "alert_count": sum(
                row["reconciliation_status"]
                != cls.STATUS_RECONCILED
                for row in rows
            ),
        }

    @classmethod
    def _reconciliation_status(
        cls,
        *,
        plan_qty,
        completed_qty,
        inventory_qty,
    ) -> str:
        if inventory_qty > completed_qty:
            return cls.STATUS_OVER
        if completed_qty > inventory_qty:
            return cls.STATUS_PENDING
        if completed_qty < plan_qty:
            return cls.STATUS_BEHIND
        return cls.STATUS_RECONCILED

    @staticmethod
    def _percentage(numerator, denominator):
        return (
            numerator / denominator * 100
            if denominator > 0
            else 0.0
        )

    @classmethod
    def _work_order_overlaps(
        cls,
        order,
        start,
        end,
    ) -> bool:
        if cls._code(
            getattr(order, "status", "")
        ) == "CANCELLED":
            return False
        start_date = cls._to_date(
            getattr(order, "start_date", None)
        )
        due_date = cls._to_date(
            getattr(order, "due_date", None)
        )
        if start_date is None or due_date is None:
            return False
        return start_date <= end and due_date >= start

    @classmethod
    def _latest_date(
        cls,
        records,
        field,
    ):
        values = [
            cls._to_date(
                getattr(record, field, None)
            )
            for record in records
        ]
        values = [
            value
            for value in values
            if value is not None
        ]
        return max(values) if values else None

    @classmethod
    def _work_order_key(cls, record):
        return (
            cls._code(
                getattr(
                    record,
                    "work_order_no",
                    "",
                )
            ),
            cls._code(
                getattr(
                    record,
                    "product_code",
                    "",
                )
            ),
        )

    @classmethod
    def _production_key(cls, record):
        return cls._work_order_key(record)

    @classmethod
    def _inventory_key(cls, record):
        return (
            cls._code(
                getattr(record, "work_order", "")
            ),
            cls._code(
                getattr(
                    record,
                    "product_code",
                    "",
                )
            ),
        )

    @staticmethod
    def _operation_number(value) -> int:
        digits = "".join(
            character
            for character in str(value or "")
            if character.isdigit()
        )
        return int(digits or 0)

    @classmethod
    def _require_date(cls, value, label):
        normalized = cls._to_date(value)
        if normalized is None:
            raise ValueError(f"{label} is required.")
        return normalized

    @staticmethod
    def _to_date(value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(
                    value[:10]
                )
            except ValueError:
                return None
        return None

    @classmethod
    def _date_in_range(
        cls,
        value,
        start,
        end,
    ) -> bool:
        normalized = cls._to_date(value)
        return (
            normalized is not None
            and start <= normalized <= end
        )

    @staticmethod
    def _code(value) -> str:
        return str(value or "").strip().upper()

    @staticmethod
    def _number(value) -> float:
        try:
            number = float(value or 0)
        except (TypeError, ValueError):
            return 0.0
        return number if isfinite(number) else 0.0

    @classmethod
    def _integer(cls, value) -> int:
        return int(round(cls._number(value)))

    def close(self) -> None:
        if self._owns_session and self.session is not None:
            self.session.close()
