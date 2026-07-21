from __future__ import annotations

from datetime import date, datetime

from src.database.session import get_session
from src.framework.base_service import BaseService
from src.framework.exception import (
    DuplicateError,
    NotFoundError,
)
from src.models.production_order import (
    ProductionOrder,
)
from src.repository.production_order_repository import (
    ProductionOrderRepository,
)


class ProductionOrderService(BaseService):
    STATUS_PLANNED = "PLANNED"
    STATUS_RELEASED = "RELEASED"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_ON_HOLD = "ON_HOLD"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"

    VALID_STATUSES = {
        STATUS_PLANNED,
        STATUS_RELEASED,
        STATUS_IN_PROGRESS,
        STATUS_ON_HOLD,
        STATUS_COMPLETED,
        STATUS_CANCELLED,
    }

    def __init__(
        self,
        session=None,
    ):
        super().__init__()

        self._owns_session = (
            session is None
        )

        self.session = (
            session
            or get_session()
        )

        self.repository = (
            ProductionOrderRepository(
                self.session
            )
        )

    # ==========================================================
    # Query
    # ==========================================================

    def get_all_production_orders(self):
        return self.repository.get_all()

    def get_production_order(
        self,
        work_order_no,
        operation_no,
    ):
        return (
            self.repository
            .get_by_work_order_operation(
                work_order_no,
                operation_no,
            )
        )

    def get_by_work_order(
        self,
        work_order_no,
    ):
        return self.repository.get_by_work_order(
            work_order_no
        )

    def get_open_orders(self):
        return self.repository.get_open_orders()

    def get_last_operation(
        self,
        work_order_no,
    ):
        return self.repository.get_last_operation(
            work_order_no
        )

    # ==========================================================
    # Create
    # ==========================================================

    def create_production_order(
        self,
        data,
    ):
        normalized = self._normalize_data(
            data
        )

        self._validate_data(
            normalized
        )

        work_order_no = normalized[
            "work_order_no"
        ]

        operation_no = normalized[
            "operation_no"
        ]

        if self.repository.exists(
            work_order_no,
            operation_no,
        ):
            raise DuplicateError(
                (
                    "Production Order already exists: "
                    f"{work_order_no} / OP{operation_no}"
                )
            )

        production_order = ProductionOrder(
            **normalized
        )

        self.log_info(
            (
                "Create Production Order: "
                f"{work_order_no} / OP{operation_no}"
            )
        )

        return self.repository.add(
            production_order
        )

    # ==========================================================
    # Update
    # ==========================================================

    def update_production_order(
        self,
        work_order_no,
        operation_no,
        data,
    ):
        production_order = (
            self.get_production_order(
                work_order_no,
                operation_no,
            )
        )

        if production_order is None:
            raise NotFoundError(
                (
                    "Production Order not found: "
                    f"{work_order_no} / OP{operation_no}"
                )
            )

        normalized = self._normalize_data(
            {
                **dict(data or {}),
                "work_order_no": (
                    production_order
                    .work_order_no
                ),
                "operation_no": (
                    production_order
                    .operation_no
                ),
            }
        )

        self._validate_data(
            normalized
        )

        for field_name in (
            "product_code",
            "operation_name",
            "process_type",
            "machine_type",
            "machine_code",
            "employee_code",
            "shift",
            "plan_qty",
            "completed_qty",
            "ng_qty",
            "status",
            "planned_start",
            "planned_finish",
            "actual_start",
            "actual_finish",
            "remark",
        ):
            setattr(
                production_order,
                field_name,
                normalized[field_name],
            )

        self.repository.update()

        return production_order

    # ==========================================================
    # Assignment
    # ==========================================================

    def assign_machine(
        self,
        work_order_no,
        operation_no,
        machine_code,
    ):
        production_order = self._require_order(
            work_order_no,
            operation_no,
        )

        production_order.machine_code = (
            self._normalize_code(
                machine_code
            )
            or None
        )

        self.repository.update()

        return production_order

    def assign_employee(
        self,
        work_order_no,
        operation_no,
        employee_code,
    ):
        production_order = self._require_order(
            work_order_no,
            operation_no,
        )

        production_order.employee_code = (
            self._normalize_code(
                employee_code
            )
            or None
        )

        self.repository.update()

        return production_order

    def assign_shift(
        self,
        work_order_no,
        operation_no,
        shift,
    ):
        production_order = self._require_order(
            work_order_no,
            operation_no,
        )

        production_order.shift = (
            self._normalize_upper(
                shift
            )
            or None
        )

        self.repository.update()

        return production_order

    # ==========================================================
    # Status workflow
    # ==========================================================

    def release(
        self,
        work_order_no,
        operation_no,
    ):
        return self.change_status(
            work_order_no,
            operation_no,
            self.STATUS_RELEASED,
        )

    def start(
        self,
        work_order_no,
        operation_no,
        actual_start=None,
    ):
        production_order = self._require_order(
            work_order_no,
            operation_no,
        )

        production_order.status = (
            self.STATUS_IN_PROGRESS
        )

        production_order.actual_start = (
            self._normalize_datetime(
                actual_start
            )
            or datetime.now()
        )

        self.repository.update()

        return production_order

    def hold(
        self,
        work_order_no,
        operation_no,
    ):
        return self.change_status(
            work_order_no,
            operation_no,
            self.STATUS_ON_HOLD,
        )

    def complete(
        self,
        work_order_no,
        operation_no,
        completed_qty=None,
        ng_qty=None,
        actual_finish=None,
    ):
        production_order = self._require_order(
            work_order_no,
            operation_no,
        )

        if completed_qty is not None:
            production_order.completed_qty = (
                self._normalize_non_negative_int(
                    completed_qty,
                    "Completed Qty",
                )
            )

        if ng_qty is not None:
            production_order.ng_qty = (
                self._normalize_non_negative_int(
                    ng_qty,
                    "NG Qty",
                )
            )

        production_order.status = (
            self.STATUS_COMPLETED
        )

        production_order.actual_finish = (
            self._normalize_datetime(
                actual_finish
            )
            or datetime.now()
        )

        self.repository.update()

        return production_order

    def cancel(
        self,
        work_order_no,
        operation_no,
    ):
        return self.change_status(
            work_order_no,
            operation_no,
            self.STATUS_CANCELLED,
        )

    def change_status(
        self,
        work_order_no,
        operation_no,
        status,
    ):
        production_order = self._require_order(
            work_order_no,
            operation_no,
        )

        production_order.status = (
            self._normalize_status(
                status
            )
        )

        self.repository.update()

        return production_order

    # ==========================================================
    # Quantity
    # ==========================================================

    def update_quantities(
        self,
        work_order_no,
        operation_no,
        completed_qty,
        ng_qty,
    ):
        production_order = self._require_order(
            work_order_no,
            operation_no,
        )

        production_order.completed_qty = (
            self._normalize_non_negative_int(
                completed_qty,
                "Completed Qty",
            )
        )

        production_order.ng_qty = (
            self._normalize_non_negative_int(
                ng_qty,
                "NG Qty",
            )
        )

        self.repository.update()

        return production_order

    # ==========================================================
    # Transaction
    # ==========================================================

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        if self._owns_session:
            self.session.close()

    # ==========================================================
    # Internal
    # ==========================================================

    def _require_order(
        self,
        work_order_no,
        operation_no,
    ):
        production_order = (
            self.get_production_order(
                work_order_no,
                operation_no,
            )
        )

        if production_order is None:
            raise NotFoundError(
                (
                    "Production Order not found: "
                    f"{work_order_no} / OP{operation_no}"
                )
            )

        return production_order

    @classmethod
    def _validate_data(
        cls,
        data,
    ):
        if not data["work_order_no"]:
            raise ValueError(
                "Work Order No is required."
            )

        if not data["product_code"]:
            raise ValueError(
                "Product Code is required."
            )

        if data["operation_no"] <= 0:
            raise ValueError(
                (
                    "Operation No must be "
                    "greater than zero."
                )
            )

        if not data["operation_name"]:
            raise ValueError(
                "Operation Name is required."
            )

        if not data["process_type"]:
            raise ValueError(
                "Process Type is required."
            )

        if data["plan_qty"] <= 0:
            raise ValueError(
                (
                    "Plan Qty must be "
                    "greater than zero."
                )
            )

        if (
            data["completed_qty"]
            + data["ng_qty"]
            > data["plan_qty"]
        ):
            raise ValueError(
                (
                    "Completed Qty + NG Qty cannot "
                    "be greater than Plan Qty."
                )
            )

        if (
            data["planned_start"] is not None
            and data["planned_finish"] is not None
            and data["planned_finish"]
            < data["planned_start"]
        ):
            raise ValueError(
                (
                    "Planned Finish cannot be "
                    "before Planned Start."
                )
            )

    @classmethod
    def _normalize_data(
        cls,
        data,
    ):
        data = dict(
            data or {}
        )

        return {
            "work_order_no": (
                cls._normalize_code(
                    data.get(
                        "work_order_no"
                    )
                )
            ),
            "product_code": (
                cls._normalize_code(
                    data.get(
                        "product_code"
                    )
                )
            ),
            "operation_no": (
                cls._normalize_operation_no(
                    data.get(
                        "operation_no"
                    )
                )
            ),
            "operation_name": (
                cls._clean_text(
                    data.get(
                        "operation_name"
                    )
                )
            ),
            "process_type": (
                cls._normalize_upper(
                    data.get(
                        "process_type"
                    )
                )
            ),
            "machine_type": (
                cls._clean_optional_upper(
                    data.get(
                        "machine_type"
                    )
                )
            ),
            "machine_code": (
                cls._clean_optional_upper(
                    data.get(
                        "machine_code"
                    )
                )
            ),
            "employee_code": (
                cls._clean_optional_upper(
                    data.get(
                        "employee_code"
                    )
                )
            ),
            "shift": (
                cls._clean_optional_upper(
                    data.get(
                        "shift"
                    )
                )
            ),
            "plan_qty": (
                cls._normalize_positive_int(
                    data.get(
                        "plan_qty"
                    ),
                    "Plan Qty",
                )
            ),
            "completed_qty": (
                cls._normalize_non_negative_int(
                    data.get(
                        "completed_qty",
                        0,
                    ),
                    "Completed Qty",
                )
            ),
            "ng_qty": (
                cls._normalize_non_negative_int(
                    data.get(
                        "ng_qty",
                        0,
                    ),
                    "NG Qty",
                )
            ),
            "status": (
                cls._normalize_status(
                    data.get(
                        "status"
                    )
                )
            ),
            "planned_start": (
                cls._normalize_datetime(
                    data.get(
                        "planned_start"
                    )
                )
            ),
            "planned_finish": (
                cls._normalize_datetime(
                    data.get(
                        "planned_finish"
                    )
                )
            ),
            "actual_start": (
                cls._normalize_datetime(
                    data.get(
                        "actual_start"
                    )
                )
            ),
            "actual_finish": (
                cls._normalize_datetime(
                    data.get(
                        "actual_finish"
                    )
                )
            ),
            "remark": (
                cls._clean_optional_text(
                    data.get(
                        "remark"
                    )
                )
            ),
        }

    @staticmethod
    def _normalize_code(
        value,
    ):
        return str(
            value or ""
        ).strip().upper()

    @staticmethod
    def _normalize_upper(
        value,
    ):
        return str(
            value or ""
        ).strip().upper()

    @staticmethod
    def _clean_text(
        value,
    ):
        return str(
            value or ""
        ).strip()

    @staticmethod
    def _clean_optional_text(
        value,
    ):
        text = str(
            value or ""
        ).strip()

        return text or None

    @staticmethod
    def _clean_optional_upper(
        value,
    ):
        text = str(
            value or ""
        ).strip().upper()

        return text or None

    @staticmethod
    def _normalize_operation_no(
        value,
    ):
        text = str(
            value or ""
        ).strip().upper()

        if text.startswith(
            "OP"
        ):
            text = text[2:].strip()

        try:
            operation_no = int(
                float(text)
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                (
                    "Invalid Operation No: "
                    f"{value}"
                )
            ) from error

        if operation_no <= 0:
            raise ValueError(
                (
                    "Operation No must be "
                    "greater than zero."
                )
            )

        return operation_no

    @staticmethod
    def _normalize_positive_int(
        value,
        field_name,
    ):
        try:
            number = int(
                float(value)
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                (
                    f"Invalid {field_name}: "
                    f"{value}"
                )
            ) from error

        if number <= 0:
            raise ValueError(
                (
                    f"{field_name} must be "
                    "greater than zero."
                )
            )

        return number

    @staticmethod
    def _normalize_non_negative_int(
        value,
        field_name,
    ):
        try:
            number = int(
                float(
                    value or 0
                )
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                (
                    f"Invalid {field_name}: "
                    f"{value}"
                )
            ) from error

        if number < 0:
            raise ValueError(
                (
                    f"{field_name} cannot "
                    "be negative."
                )
            )

        return number

    @classmethod
    def _normalize_status(
        cls,
        value,
    ):
        status = str(
            value
            or cls.STATUS_PLANNED
        ).strip().upper()

        if status not in cls.VALID_STATUSES:
            raise ValueError(
                (
                    "Invalid Production Order "
                    f"Status: {status}"
                )
            )

        return status

    @staticmethod
    def _normalize_datetime(
        value,
    ):
        if value is None or value == "":
            return None

        if isinstance(
            value,
            datetime,
        ):
            return value

        if isinstance(
            value,
            date,
        ):
            return datetime.combine(
                value,
                datetime.min.time(),
            )

        text = str(
            value
        ).strip()

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
        ]

        for date_format in formats:
            try:
                return datetime.strptime(
                    text,
                    date_format,
                )
            except ValueError:
                continue

        try:
            return datetime.fromisoformat(
                text
            )
        except ValueError as error:
            raise ValueError(
                (
                    "Invalid datetime value: "
                    f"{value}"
                )
            ) from error