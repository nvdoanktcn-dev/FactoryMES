from src.database.session import get_session
from src.framework.exception import (
    NotFoundError,
    ValidationError,
)
from src.repository.product_repository import ProductRepository
from src.repository.work_order_repository import WorkOrderRepository
from src.schema.work_order_schema import WorkOrderSchema


class WorkOrderValidator:
    """
    Kiểm tra nghiệp vụ Work Order trước khi ghi database.

    Validator:
    - Có thể đọc database.
    - Không ghi hoặc cập nhật database.
    """

    def __init__(self, session=None):
        self.session = session or get_session()

        self.product_repository = ProductRepository(
            self.session
        )

        self.work_order_repository = WorkOrderRepository(
            self.session
        )

    def validate(
        self,
        data,
        allow_existing=True,
    ):
        """
        Kiểm tra một Work Order đã được Mapper chuẩn hóa.
        """
        if not isinstance(data, dict):
            raise ValidationError(
                "Work Order data must be a dictionary."
            )

        WorkOrderSchema.validate_data(data)

        work_order_no = str(
            data.get("work_order_no", "")
        ).strip().upper()

        product_code = str(
            data.get("product_code", "")
        ).strip().upper()

        product = self.product_repository.get_by_code(
            product_code
        )

        if product is None:
            raise NotFoundError(
                f"Product not found: {product_code}"
            )

        existing = self.work_order_repository.get_by_no(
            work_order_no
        )

        if existing is not None and not allow_existing:
            raise ValidationError(
                f"Work Order already exists: {work_order_no}"
            )

        self.validate_quantities(data)
        self.validate_dates(data)
        self.validate_status_consistency(data)

        return True

    @staticmethod
    def validate_quantities(data):
        plan_qty = int(data.get("plan_qty") or 0)
        completed_qty = int(
            data.get("completed_qty") or 0
        )
        ng_qty = int(data.get("ng_qty") or 0)

        if plan_qty <= 0:
            raise ValidationError(
                "Plan Qty must be greater than zero."
            )

        if completed_qty < 0:
            raise ValidationError(
                "Completed Qty cannot be negative."
            )

        if ng_qty < 0:
            raise ValidationError(
                "NG Qty cannot be negative."
            )

        if completed_qty > plan_qty:
            raise ValidationError(
                "Completed Qty cannot exceed Plan Qty."
            )

        if ng_qty > plan_qty:
            raise ValidationError(
                "NG Qty cannot exceed Plan Qty."
            )

    @staticmethod
    def validate_dates(data):
        start_date = data.get("start_date")
        due_date = data.get("due_date")
        finish_date = data.get("finish_date")

        if (
            start_date is not None
            and due_date is not None
            and due_date < start_date
        ):
            raise ValidationError(
                "Due Date cannot be earlier than Start Date."
            )

        if (
            start_date is not None
            and finish_date is not None
            and finish_date < start_date
        ):
            raise ValidationError(
                "Finish Date cannot be earlier than Start Date."
            )

        if (
            due_date is not None
            and finish_date is not None
            and finish_date > due_date
        ):
            # Đây chỉ là cảnh báo nghiệp vụ trong nhiều nhà máy,
            # nhưng hiện tại chưa chặn vì Work Order có thể trễ hạn.
            pass

    @staticmethod
    def validate_status_consistency(data):
        status = str(
            data.get("status", "PLANNED")
        ).strip().upper()

        completed_qty = int(
            data.get("completed_qty") or 0
        )

        finish_date = data.get("finish_date")

        if status == "COMPLETED" and completed_qty <= 0:
            raise ValidationError(
                "Completed Work Order must have "
                "Completed Qty greater than zero."
            )

        if status == "COMPLETED" and finish_date is None:
            raise ValidationError(
                "Completed Work Order requires Finish Date."
            )

        if status in {"PLANNED", "RELEASED"} and finish_date is not None:
            raise ValidationError(
                f"Work Order with status {status} "
                "cannot have Finish Date."
            )

    def validate_dataframe_records(self, records):
        """
        Kiểm tra Work Order No trùng ngay trong file import.
        """
        errors = []
        seen_work_orders = set()

        for record in records:
            excel_row = record["excel_row"]
            data = record["data"]

            work_order_no = str(
                data.get("work_order_no", "")
            ).strip().upper()

            if work_order_no in seen_work_orders:
                errors.append({
                    "row": excel_row,
                    "message": (
                        "Duplicate Work Order No "
                        f"inside import file: {work_order_no}"
                    ),
                })
            else:
                seen_work_orders.add(work_order_no)

        return errors