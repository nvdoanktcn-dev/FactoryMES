from datetime import datetime

from src.controllers.employee_controller import EmployeeController
from src.controllers.machine_controller import MachineController
from src.controllers.work_order_controller import WorkOrderController
from src.framework.exception import NotFoundError, ValidationError
from src.services.production_log_service import ProductionLogService
from src.utils.production_hash import create_production_record_hash


class ProductionEngine:
    """
    Xử lý nghiệp vụ cho một bản ghi sản xuất chuẩn.

    Luồng xử lý:

        Production DTO
            -> Chuẩn hóa dữ liệu
            -> Kiểm tra Work Order
            -> Kiểm tra Machine
            -> Kiểm tra Employee
            -> Kiểm tra số lượng
            -> Xác định runtime
            -> Tạo record_hash
            -> Kiểm tra trùng bản ghi
            -> Lưu ProductionLog
            -> Cập nhật tiến độ Work Order
    """

    VALID_WORK_ORDER_STATUSES = {
        "RELEASED",
        "RUNNING",
        "PAUSED",
    }

    def __init__(self):
        self.work_order_controller = WorkOrderController()
        self.machine_controller = MachineController()
        self.employee_controller = EmployeeController()
        self.production_service = ProductionLogService()

    # ==========================================================
    # Main process
    # ==========================================================

    def process_log(self, data):
        """
        Xử lý và lưu một bản ghi sản xuất.

        Args:
            data: Dictionary chuẩn được tạo bởi ProductionMapper.

        Returns:
            ProductionLog vừa được lưu.

        Raises:
            ValidationError:
                Khi dữ liệu không hợp lệ hoặc bị trùng.

            NotFoundError:
                Khi Work Order, Machine hoặc Employee không tồn tại.
        """
        normalized_data = self.normalize_data(data)

        work_order = self.validate_work_order(
            normalized_data["work_order_no"]
        )

        self.validate_product(
            work_order=work_order,
            product_code=normalized_data["product_code"],
        )

        self.validate_machine(
            normalized_data["machine_code"]
        )

        self.validate_employee(
            normalized_data["employee_code"]
        )

        self.validate_operation(
            normalized_data["op_no"]
        )

        self.validate_quantities(normalized_data)

        normalized_data["run_time_sec"] = self.resolve_runtime(
            start_time=normalized_data.get("start_time"),
            finish_time=normalized_data.get("finish_time"),
            supplied_runtime=normalized_data.get("run_time_sec"),
        )

        normalized_data["record_hash"] = (
            create_production_record_hash(normalized_data)
        )

        self.validate_duplicate_record(
            normalized_data["record_hash"]
        )

        log = self.production_service.create(
            normalized_data
        )

        try:
            self.work_order_controller.update_progress(
                normalized_data["work_order_no"],
                normalized_data["ok_qty"],
                normalized_data["ng_qty"],
            )

        except Exception as error:
            # ProductionLog đã được tạo nhưng cập nhật tiến độ
            # Work Order thất bại.
            raise ValidationError(
                "Production Log was created, but Work Order progress "
                "could not be updated."
            ) from error

        return log

    # ==========================================================
    # Normalize
    # ==========================================================

    @classmethod
    def normalize_data(cls, data):
        if not isinstance(data, dict):
            raise ValidationError(
                "Production data must be a dictionary."
            )

        normalized = dict(data)

        text_fields = [
            "work_order_no",
            "product_code",
            "op_no",
            "machine_code",
            "employee_code",
            "shift",
            "downtime_reason",
            "status",
            "remark",
        ]

        for field in text_fields:
            normalized[field] = cls.clean_text(
                normalized.get(field)
            )

        uppercase_fields = [
            "work_order_no",
            "product_code",
            "op_no",
            "machine_code",
            "employee_code",
            "shift",
            "status",
        ]

        for field in uppercase_fields:
            normalized[field] = (
                normalized.get(field, "").upper()
            )

        normalized["op_no"] = cls.normalize_op(
            normalized.get("op_no")
        )

        normalized["shift"] = cls.normalize_shift(
            normalized.get("shift")
        )

        normalized["ok_qty"] = cls.to_non_negative_int(
            normalized.get("ok_qty")
        )

        normalized["ng_qty"] = cls.to_non_negative_int(
            normalized.get("ng_qty")
        )

        normalized["run_time_sec"] = cls.to_non_negative_float(
            normalized.get("run_time_sec")
        )

        normalized["downtime_min"] = cls.to_non_negative_float(
            normalized.get("downtime_min")
        )

        normalized["start_time"] = cls.to_datetime(
            normalized.get("start_time")
        )

        normalized["finish_time"] = cls.to_datetime(
            normalized.get("finish_time")
        )

        if not normalized["status"]:
            normalized["status"] = "COMPLETED"

        return normalized

    # ==========================================================
    # Work Order validation
    # ==========================================================

    def validate_work_order(self, work_order_no):
        if not work_order_no:
            raise ValidationError(
                "Work Order No is required."
            )

        work_order = self.work_order_controller.get_by_no(
            work_order_no
        )

        if work_order is None:
            raise NotFoundError(
                f"Work Order does not exist: {work_order_no}"
            )

        status = self.clean_text(
            getattr(work_order, "status", "")
        ).upper()

        if status not in self.VALID_WORK_ORDER_STATUSES:
            raise ValidationError(
                f"Work Order {work_order_no} cannot receive "
                f"production data while status is "
                f"{status or 'EMPTY'}."
            )

        return work_order

    @classmethod
    def validate_product(cls, work_order, product_code):
        if not product_code:
            raise ValidationError(
                "Product Code is required."
            )

        work_order_product = cls.clean_text(
            getattr(work_order, "product_code", "")
        ).upper()

        if (
            work_order_product
            and product_code != work_order_product
        ):
            raise ValidationError(
                f"Product {product_code} does not match "
                f"Work Order product {work_order_product}."
            )

    # ==========================================================
    # Machine validation
    # ==========================================================

    def validate_machine(self, machine_code):
        if not machine_code:
            raise ValidationError(
                "Machine Code is required."
            )

        machine = self.machine_controller.get_by_code(
            machine_code
        )

        if machine is None:
            raise NotFoundError(
                f"Machine does not exist: {machine_code}"
            )

        status = self.clean_text(
            getattr(machine, "status", "")
        ).upper()

        if status == "INACTIVE":
            raise ValidationError(
                f"Machine is inactive: {machine_code}"
            )

        return machine

    # ==========================================================
    # Employee validation
    # ==========================================================

    def validate_employee(self, employee_code):
        if not employee_code:
            raise ValidationError(
                "Employee Code is required."
            )

        employee = self.employee_controller.get_by_code(
            employee_code
        )

        if employee is None:
            raise NotFoundError(
                f"Employee does not exist: {employee_code}"
            )

        status = self.clean_text(
            getattr(employee, "status", "")
        ).upper()

        if status == "INACTIVE":
            raise ValidationError(
                f"Employee is inactive: {employee_code}"
            )

        return employee

    # ==========================================================
    # Operation validation
    # ==========================================================

    @staticmethod
    def validate_operation(op_no):
        if not op_no:
            raise ValidationError(
                "Operation No is required."
            )

        if not op_no.startswith("OP"):
            raise ValidationError(
                f"Invalid operation format: {op_no}"
            )

        op_number = op_no[2:]

        if not op_number.isdigit():
            raise ValidationError(
                f"Invalid operation format: {op_no}"
            )

    # ==========================================================
    # Quantity validation
    # ==========================================================

    @staticmethod
    def validate_quantities(data):
        ok_qty = data.get("ok_qty", 0)
        ng_qty = data.get("ng_qty", 0)

        if ok_qty < 0:
            raise ValidationError(
                "OK quantity cannot be negative."
            )

        if ng_qty < 0:
            raise ValidationError(
                "NG quantity cannot be negative."
            )

        if ok_qty == 0 and ng_qty == 0:
            raise ValidationError(
                "OK quantity and NG quantity "
                "cannot both be zero."
            )

    # ==========================================================
    # Duplicate validation
    # ==========================================================

    def validate_duplicate_record(self, record_hash):
        if not record_hash:
            raise ValidationError(
                "Production record hash is required."
            )

        existing_log = (
            self.production_service.get_by_record_hash(
                record_hash
            )
        )

        if existing_log is not None:
            raise ValidationError(
                "Duplicate production record detected."
            )

    # ==========================================================
    # Runtime
    # ==========================================================

    @classmethod
    def resolve_runtime(
        cls,
        start_time=None,
        finish_time=None,
        supplied_runtime=0,
    ):
        """
        Ưu tiên tính runtime từ thời gian bắt đầu/kết thúc.

        Nếu không có đủ start_time và finish_time,
        sử dụng run_time_sec do ProductionMapper cung cấp.
        """
        if (
            start_time is not None
            and finish_time is not None
        ):
            runtime = cls.calculate_runtime(
                start_time,
                finish_time,
            )

            if runtime > 0:
                return runtime

        runtime = cls.to_non_negative_float(
            supplied_runtime
        )

        if runtime <= 0:
            raise ValidationError(
                "Runtime is required. Provide start/finish "
                "time or a positive run_time_sec value."
            )

        return runtime

    @classmethod
    def calculate_runtime(
        cls,
        start_time,
        finish_time,
    ):
        start = cls.to_datetime(start_time)
        finish = cls.to_datetime(finish_time)

        if start is None or finish is None:
            return 0.0

        runtime = (
            finish - start
        ).total_seconds()

        if runtime < 0:
            raise ValidationError(
                "Finish time cannot be earlier "
                "than start time."
            )

        return float(runtime)

    # ==========================================================
    # Conversion helpers
    # ==========================================================

    @staticmethod
    def clean_text(value):
        if value is None:
            return ""

        text = str(value).strip()

        if text.lower() in {
            "nan",
            "none",
            "nat",
        }:
            return ""

        return text

    @classmethod
    def normalize_op(cls, value):
        text = cls.clean_text(value).upper()

        if not text:
            return ""

        digits = "".join(
            character
            for character in text
            if character.isdigit()
        )

        if digits:
            return f"OP{int(digits)}"

        return text

    @classmethod
    def normalize_shift(cls, value):
        text = cls.clean_text(value).upper()

        mapping = {
            "DAY": "DAY",
            "D": "DAY",
            "NGÀY": "DAY",
            "CA NGÀY": "DAY",

            "NIGHT": "NIGHT",
            "N": "NIGHT",
            "ĐÊM": "NIGHT",
            "CA ĐÊM": "NIGHT",

            "ADMIN": "ADMIN",
            "HÀNH CHÍNH": "ADMIN",
        }

        return mapping.get(text, text)

    @staticmethod
    def to_datetime(value):
        if value is None or value == "":
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            text = value.strip()

            if not text:
                return None

            try:
                return datetime.fromisoformat(text)

            except ValueError as error:
                raise ValidationError(
                    f"Invalid datetime value: {value}"
                ) from error

        if hasattr(value, "to_pydatetime"):
            return value.to_pydatetime()

        raise ValidationError(
            f"Unsupported datetime type: "
            f"{type(value).__name__}"
        )

    @staticmethod
    def to_non_negative_int(value):
        if value is None or value == "":
            return 0

        try:
            number = int(float(value))

        except (TypeError, ValueError) as error:
            raise ValidationError(
                f"Invalid integer value: {value}"
            ) from error

        if number < 0:
            raise ValidationError(
                f"Value cannot be negative: {value}"
            )

        return number

    @staticmethod
    def to_non_negative_float(value):
        if value is None or value == "":
            return 0.0

        try:
            number = float(value)

        except (TypeError, ValueError) as error:
            raise ValidationError(
                f"Invalid numeric value: {value}"
            ) from error

        if number < 0:
            raise ValidationError(
                f"Value cannot be negative: {value}"
            )

        return number