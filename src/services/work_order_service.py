from __future__ import annotations

from datetime import date, datetime

from src.database.session import get_session
from src.framework.base_service import BaseService
from src.framework.exception import (
    DuplicateError,
    NotFoundError,
)
from src.framework.validator import BaseValidator
from src.models.work_order import WorkOrder
from src.repository.work_order_repository import (
    WorkOrderRepository,
)
from src.services.product_service import (
    ProductService,
)


class WorkOrderService(BaseService):
    PRIORITY_LOW = "LOW"
    PRIORITY_NORMAL = "NORMAL"
    PRIORITY_HIGH = "HIGH"
    PRIORITY_URGENT = "URGENT"

    VALID_PRIORITIES = {
        PRIORITY_LOW,
        PRIORITY_NORMAL,
        PRIORITY_HIGH,
        PRIORITY_URGENT,
    }

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

        self.repository = WorkOrderRepository(
            self.session
        )

        self.product_service = ProductService(
            session=self.session
        )

    # ==========================================================
    # Query
    # ==========================================================

    def get_all_work_orders(self):
        return self.repository.get_all()

    def get_work_order(
        self,
        work_order_no,
    ):
        number = self._normalize_work_order_no(
            work_order_no
        )

        if not number:
            return None

        return self.repository.get_by_no(
            number
        )

    def get_by_no(
        self,
        work_order_no,
    ):
        return self.get_work_order(
            work_order_no
        )

    def get_by_product(
        self,
        product_code,
    ):
        return self.repository.get_by_product(
            product_code
        )

    def get_by_status(
        self,
        status,
    ):
        return self.repository.get_by_status(
            status
        )

    def get_open_orders(self):
        return self.repository.get_open_orders()

    # ==========================================================
    # Create
    # ==========================================================

    def create_work_order(
        self,
        data,
    ):
        normalized = self._normalize_data(
            data
        )

        self._validate_work_order(
            normalized
        )

        work_order_no = normalized[
            "work_order_no"
        ]

        if self.repository.exists(
            work_order_no
        ):
            raise DuplicateError(
                (
                    "Work Order already exists: "
                    f"{work_order_no}"
                )
            )

        self._validate_product_exists(
            normalized["product_code"]
        )

        work_order = WorkOrder(
            work_order_no=normalized[
                "work_order_no"
            ],
            product_code=normalized[
                "product_code"
            ],
            plan_qty=normalized[
                "plan_qty"
            ],
            start_date=normalized[
                "start_date"
            ],
            due_date=normalized[
                "due_date"
            ],
            priority=normalized[
                "priority"
            ],
            status=normalized[
                "status"
            ],
            remark=normalized[
                "remark"
            ],
        )

        self.log_info(
            (
                "Create Work Order: "
                f"{work_order_no}"
            )
        )

        return self.repository.add(
            work_order
        )

    # ==========================================================
    # Update
    # ==========================================================

    def update_work_order(
        self,
        work_order_no,
        data,
    ):
        number = self._normalize_work_order_no(
            work_order_no
        )

        work_order = self.repository.get_by_no(
            number
        )

        if work_order is None:
            raise NotFoundError(
                (
                    "Work Order not found: "
                    f"{number}"
                )
            )

        normalized = self._normalize_data(
            {
                **dict(data or {}),
                "work_order_no": number,
            }
        )

        self._validate_work_order(
            normalized
        )

        self._validate_product_exists(
            normalized["product_code"]
        )

        work_order.product_code = normalized[
            "product_code"
        ]

        work_order.plan_qty = normalized[
            "plan_qty"
        ]

        work_order.start_date = normalized[
            "start_date"
        ]

        work_order.due_date = normalized[
            "due_date"
        ]

        work_order.priority = normalized[
            "priority"
        ]

        work_order.status = normalized[
            "status"
        ]

        work_order.remark = normalized[
            "remark"
        ]

        self.repository.update()

        return work_order

    # ==========================================================
    # Upsert for Master Import
    # ==========================================================

    def save_work_order(
        self,
        data,
    ):
        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                "Work Order data must be a dictionary."
            )

        work_order_no = (
            self._normalize_work_order_no(
                data.get(
                    "work_order_no"
                )
            )
        )

        existing = self.repository.get_by_no(
            work_order_no
        )

        if existing is None:
            work_order = self.create_work_order(
                data
            )

            return work_order, "created"

        work_order = self.update_work_order(
            work_order_no,
            data,
        )

        return work_order, "updated"

    # ==========================================================
    # Status operations
    # ==========================================================

    def release_work_order(
        self,
        work_order_no,
    ):
        return self.change_status(
            work_order_no,
            self.STATUS_RELEASED,
        )

    def start_work_order(
        self,
        work_order_no,
    ):
        return self.change_status(
            work_order_no,
            self.STATUS_IN_PROGRESS,
        )

    def complete_work_order(
        self,
        work_order_no,
    ):
        return self.change_status(
            work_order_no,
            self.STATUS_COMPLETED,
        )

    def hold_work_order(
        self,
        work_order_no,
    ):
        return self.change_status(
            work_order_no,
            self.STATUS_ON_HOLD,
        )

    def delete_work_order(
        self,
        work_order_no,
    ):
        return self.change_status(
            work_order_no,
            self.STATUS_CANCELLED,
        )

    def change_status(
        self,
        work_order_no,
        status,
    ):
        number = self._normalize_work_order_no(
            work_order_no
        )

        normalized_status = (
            self._normalize_status(
                status
            )
        )

        work_order = self.repository.get_by_no(
            number
        )

        if work_order is None:
            raise NotFoundError(
                (
                    "Work Order not found: "
                    f"{number}"
                )
            )

        work_order.status = normalized_status

        self.repository.update()

        return work_order

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
    # Validation
    # ==========================================================

    def _validate_product_exists(
        self,
        product_code,
    ):
        product = self.product_service.get_product(
            product_code
        )

        if product is None:
            raise ValueError(
                (
                    "Product does not exist: "
                    f"{product_code}"
                )
            )

    @classmethod
    def _validate_work_order(
        cls,
        data,
    ):
        BaseValidator.required(
            data["work_order_no"],
            "Work Order No",
        )

        BaseValidator.required(
            data["product_code"],
            "Product Code",
        )

        if data["plan_qty"] <= 0:
            raise ValueError(
                (
                    "Plan Qty must be "
                    "greater than zero."
                )
            )

        if data["due_date"] < data["start_date"]:
            raise ValueError(
                (
                    "Due Date cannot be before "
                    "Start Date."
                )
            )

    # ==========================================================
    # Normalization
    # ==========================================================

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
                cls._normalize_work_order_no(
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
            "plan_qty": (
                cls._normalize_quantity(
                    data.get(
                        "plan_qty"
                    )
                )
            ),
            "start_date": (
                cls._normalize_date(
                    data.get(
                        "start_date"
                    ),
                    "Start Date",
                )
            ),
            "due_date": (
                cls._normalize_date(
                    data.get(
                        "due_date"
                    ),
                    "Due Date",
                )
            ),
            "priority": (
                cls._normalize_priority(
                    data.get(
                        "priority"
                    )
                )
            ),
            "status": (
                cls._normalize_status(
                    data.get(
                        "status"
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
    def _normalize_work_order_no(
        value,
    ):
        return str(
            value or ""
        ).strip().upper()

    @staticmethod
    def _normalize_code(
        value,
    ):
        return str(
            value or ""
        ).strip().upper()

    @staticmethod
    def _normalize_quantity(
        value,
    ):
        try:
            quantity = int(
                float(value)
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                (
                    "Invalid Plan Qty: "
                    f"{value}"
                )
            ) from error

        if quantity <= 0:
            raise ValueError(
                (
                    "Plan Qty must be "
                    "greater than zero."
                )
            )

        return quantity

    @staticmethod
    def _normalize_date(
        value,
        field_name,
    ):
        if isinstance(
            value,
            datetime,
        ):
            return value.date()

        if isinstance(
            value,
            date,
        ):
            return value

        text = str(
            value or ""
        ).strip()

        if not text:
            raise ValueError(
                f"{field_name} is required."
            )

        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
        ]

        for date_format in formats:
            try:
                return datetime.strptime(
                    text,
                    date_format,
                ).date()
            except ValueError:
                continue

        raise ValueError(
            (
                f"Invalid {field_name}: {value}. "
                "Supported formats: YYYY-MM-DD "
                "or DD/MM/YYYY."
            )
        )

    @classmethod
    def _normalize_priority(
        cls,
        value,
    ):
        priority = str(
            value
            or cls.PRIORITY_NORMAL
        ).strip().upper()

        if priority not in cls.VALID_PRIORITIES:
            raise ValueError(
                (
                    "Invalid Work Order Priority: "
                    f"{priority}"
                )
            )

        return priority

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
                    "Invalid Work Order Status: "
                    f"{status}"
                )
            )

        return status

    @staticmethod
    def _clean_optional_text(
        value,
    ):
        text = str(
            value or ""
        ).strip()

        return text or None