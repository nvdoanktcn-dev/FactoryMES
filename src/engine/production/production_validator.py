from datetime import datetime
from hashlib import sha256

from src.engine.production.dto import (
    ProductionValidationResult,
)


class ProductionValidator:
    """
    Pure validator cho Production Entry.

    Không query database và không commit.

    Input:
        data:
            dictionary dữ liệu Production Entry.

        work_order:
            WorkOrder object hoặc None.

        routing:
            Routing object hoặc None.

        machine:
            Machine object hoặc None.

        existing_record_hashes:
            tập hash đã có để kiểm tra trùng.

    Quy tắc:
        - Work Order tồn tại và còn hiệu lực.
        - Product khớp Work Order.
        - OP thuộc Routing.
        - Machine tồn tại.
        - Machine Code/Type khớp Routing.
        - Start Time phải trước Finish Time.
        - OK/NG không âm và tổng sản lượng > 0.
        - Runtime hợp lệ.
        - Không trùng record_hash.
    """

    ALLOWED_WORK_ORDER_STATUSES = {
        "RELEASED",
        "RUNNING",
        "PAUSED",
    }

    BLOCKED_WORK_ORDER_STATUSES = {
        "COMPLETED",
        "CLOSED",
        "CANCELLED",
    }

    ACTIVE_MACHINE_STATUSES = {
        "ACTIVE",
        "RUNNING",
        "READY",
        "MAINTENANCE",
    }

    def validate(
        self,
        data,
        work_order=None,
        routing=None,
        machine=None,
        existing_record_hashes=None,
    ):
        result = ProductionValidationResult()

        if not isinstance(data, dict):
            result.add_error(
                code="INVALID_DATA_TYPE",
                message=(
                    "Production data must be a dictionary."
                ),
            )
            return result

        normalized = self.normalize_data(data)
        result.normalized_data = normalized

        self._validate_required_fields(
            normalized,
            result,
        )

        self._validate_quantities(
            normalized,
            result,
        )

        self._validate_time(
            normalized,
            result,
        )

        self._validate_work_order(
            normalized,
            work_order,
            result,
        )

        self._validate_routing(
            normalized,
            routing,
            result,
        )

        self._validate_machine(
            normalized,
            machine,
            routing,
            result,
        )

        self._validate_duplicate(
            normalized,
            existing_record_hashes or set(),
            result,
        )

        return result

    # ==========================================================
    # Normalization
    # ==========================================================

    def normalize_data(self, data):
        start_time = self._to_datetime(
            data.get("start_time")
        )

        finish_time = self._to_datetime(
            data.get("finish_time")
            or data.get("end_time")
        )

        runtime_sec = self._to_non_negative_float(
            data.get("run_time_sec")
            or data.get("runtime_sec")
            or 0
        )

        if (
            runtime_sec <= 0
            and start_time is not None
            and finish_time is not None
        ):
            runtime_sec = max(
                (
                    finish_time
                    - start_time
                ).total_seconds(),
                0.0,
            )

        normalized = {
            "record_hash": self._normalize_text(
                data.get("record_hash")
            ).lower(),

            "work_order_no": self._normalize_code(
                data.get("work_order_no")
            ),

            "product_code": self._normalize_code(
                data.get("product_code")
            ),

            "op_no": self._normalize_op(
                data.get("op_no")
            ),

            "machine_code": self._normalize_code(
                data.get("machine_code")
            ),

            "employee_code": self._normalize_code(
                data.get("employee_code")
                or data.get("operator_code")
            ),

            "shift": self._normalize_shift(
                data.get("shift")
            ),

            "start_time": start_time,
            "finish_time": finish_time,
            "run_time_sec": runtime_sec,

            "ok_qty": self._to_non_negative_int(
                data.get("ok_qty")
            ),

            "ng_qty": self._to_non_negative_int(
                data.get("ng_qty")
            ),

            "downtime_min":
                self._to_non_negative_float(
                    data.get("downtime_min")
                ),

            "downtime_reason":
                self._normalize_text(
                    data.get("downtime_reason")
                ),

            "status": self._normalize_code(
                data.get("status")
                or "COMPLETED"
            ),

            "remark": self._normalize_text(
                data.get("remark")
            ),
        }

        if not normalized["record_hash"]:
            normalized["record_hash"] = (
                self.build_record_hash(
                    normalized
                )
            )

        return normalized

    # ==========================================================
    # Required fields
    # ==========================================================

    @staticmethod
    def _validate_required_fields(
        data,
        result,
    ):
        required_fields = {
            "work_order_no": "Work Order No",
            "product_code": "Product Code",
            "op_no": "OP No",
            "machine_code": "Machine Code",
            "employee_code": "Employee Code",
        }

        for field, label in required_fields.items():
            if not data.get(field):
                result.add_error(
                    code="REQUIRED_FIELD",
                    message=f"{label} is required.",
                    field=field,
                )

    # ==========================================================
    # Quantity validation
    # ==========================================================

    @staticmethod
    def _validate_quantities(
        data,
        result,
    ):
        ok_qty = data["ok_qty"]
        ng_qty = data["ng_qty"]

        if ok_qty < 0:
            result.add_error(
                code="NEGATIVE_OK_QTY",
                message="OK Qty cannot be negative.",
                field="ok_qty",
            )

        if ng_qty < 0:
            result.add_error(
                code="NEGATIVE_NG_QTY",
                message="NG Qty cannot be negative.",
                field="ng_qty",
            )

        if ok_qty + ng_qty <= 0:
            result.add_error(
                code="EMPTY_OUTPUT",
                message=(
                    "OK Qty + NG Qty must be "
                    "greater than zero."
                ),
                field="ok_qty",
            )

    # ==========================================================
    # Time validation
    # ==========================================================

    @staticmethod
    def _validate_time(
        data,
        result,
    ):
        start_time = data["start_time"]
        finish_time = data["finish_time"]
        runtime_sec = data["run_time_sec"]

        if start_time is None:
            result.add_error(
                code="START_TIME_REQUIRED",
                message="Start Time is required.",
                field="start_time",
            )

        if finish_time is None:
            result.add_error(
                code="FINISH_TIME_REQUIRED",
                message="Finish Time is required.",
                field="finish_time",
            )

        if (
            start_time is not None
            and finish_time is not None
        ):
            if finish_time <= start_time:
                result.add_error(
                    code="INVALID_TIME_RANGE",
                    message=(
                        "Finish Time must be later "
                        "than Start Time."
                    ),
                    field="finish_time",
                )

            calculated_runtime = max(
                (
                    finish_time - start_time
                ).total_seconds(),
                0.0,
            )

            if runtime_sec > calculated_runtime:
                result.add_warning(
                    code="RUNTIME_EXCEEDS_TIME_RANGE",
                    message=(
                        "Runtime exceeds the duration "
                        "between Start and Finish Time."
                    ),
                    field="run_time_sec",
                )

        if runtime_sec <= 0:
            result.add_error(
                code="INVALID_RUNTIME",
                message=(
                    "Runtime must be greater than zero."
                ),
                field="run_time_sec",
            )

    # ==========================================================
    # Work Order validation
    # ==========================================================

    def _validate_work_order(
        self,
        data,
        work_order,
        result,
    ):
        if work_order is None:
            result.add_error(
                code="WORK_ORDER_NOT_FOUND",
                message=(
                    "Work Order not found: "
                    f"{data['work_order_no']}"
                ),
                field="work_order_no",
            )
            return

        work_order_no = self._normalize_code(
            getattr(
                work_order,
                "work_order_no",
                "",
            )
        )

        if work_order_no != data["work_order_no"]:
            result.add_error(
                code="WORK_ORDER_MISMATCH",
                message=(
                    "Work Order object does not match "
                    "the Production Entry."
                ),
                field="work_order_no",
            )

        work_order_product = self._normalize_code(
            getattr(
                work_order,
                "product_code",
                "",
            )
        )

        if (
            work_order_product
            and work_order_product
            != data["product_code"]
        ):
            result.add_error(
                code="PRODUCT_MISMATCH",
                message=(
                    f"Product {data['product_code']} "
                    "does not match Work Order Product "
                    f"{work_order_product}."
                ),
                field="product_code",
            )

        status = self._normalize_code(
            getattr(
                work_order,
                "status",
                "PLANNED",
            )
        )

        if status in self.BLOCKED_WORK_ORDER_STATUSES:
            result.add_error(
                code="WORK_ORDER_NOT_EXECUTABLE",
                message=(
                    f"Work Order status {status} "
                    "does not allow production entry."
                ),
                field="work_order_no",
            )

        elif status == "PLANNED":
            result.add_warning(
                code="WORK_ORDER_NOT_RELEASED",
                message=(
                    "Work Order is still PLANNED. "
                    "It should be RELEASED before production."
                ),
                field="work_order_no",
            )

        elif (
            status
            and status not in self.ALLOWED_WORK_ORDER_STATUSES
        ):
            result.add_warning(
                code="UNKNOWN_WORK_ORDER_STATUS",
                message=(
                    f"Unknown Work Order status: {status}"
                ),
                field="work_order_no",
            )

    # ==========================================================
    # Routing validation
    # ==========================================================

    def _validate_routing(
        self,
        data,
        routing,
        result,
    ):
        if routing is None:
            result.add_error(
                code="ROUTING_NOT_FOUND",
                message=(
                    "Routing not found: "
                    f"{data['product_code']} - "
                    f"{data['op_no']}"
                ),
                field="op_no",
            )
            return

        routing_product = self._normalize_code(
            getattr(
                routing,
                "product_code",
                "",
            )
        )

        routing_op = self._normalize_op(
            getattr(
                routing,
                "op_no",
                "",
            )
        )

        if routing_product != data["product_code"]:
            result.add_error(
                code="ROUTING_PRODUCT_MISMATCH",
                message=(
                    "Routing Product does not match "
                    "Production Product."
                ),
                field="product_code",
            )

        if routing_op != data["op_no"]:
            result.add_error(
                code="ROUTING_OP_MISMATCH",
                message=(
                    "Routing OP does not match "
                    "Production OP."
                ),
                field="op_no",
            )

        routing_status = self._normalize_code(
            getattr(
                routing,
                "status",
                "ACTIVE",
            )
        )

        if routing_status != "ACTIVE":
            result.add_error(
                code="ROUTING_INACTIVE",
                message=(
                    f"Routing {routing_product} - "
                    f"{routing_op} is not ACTIVE."
                ),
                field="op_no",
            )

        cycle_time = self._to_non_negative_float(
            getattr(
                routing,
                "cycle_time_sec",
                0,
            )
        )

        if cycle_time <= 0:
            result.add_error(
                code="INVALID_ROUTING_CYCLE_TIME",
                message=(
                    "Routing Cycle Time must be "
                    "greater than zero."
                ),
                field="op_no",
            )

    # ==========================================================
    # Machine validation
    # ==========================================================

    def _validate_machine(
        self,
        data,
        machine,
        routing,
        result,
    ):
        if machine is None:
            result.add_error(
                code="MACHINE_NOT_FOUND",
                message=(
                    "Machine not found: "
                    f"{data['machine_code']}"
                ),
                field="machine_code",
            )
            return

        machine_code = self._normalize_code(
            getattr(
                machine,
                "machine_code",
                "",
            )
        )

        if machine_code != data["machine_code"]:
            result.add_error(
                code="MACHINE_OBJECT_MISMATCH",
                message=(
                    "Machine object does not match "
                    "Production Machine."
                ),
                field="machine_code",
            )

        machine_status = self._normalize_code(
            getattr(
                machine,
                "status",
                "",
            )
        )

        if (
            machine_status
            and machine_status
            not in self.ACTIVE_MACHINE_STATUSES
        ):
            result.add_error(
                code="MACHINE_NOT_AVAILABLE",
                message=(
                    f"Machine {machine_code} "
                    f"status is {machine_status}."
                ),
                field="machine_code",
            )

        if routing is None:
            return

        routing_machine_code = self._normalize_code(
            getattr(
                routing,
                "machine_code",
                "",
            )
        )

        if (
            routing_machine_code
            and routing_machine_code
            != data["machine_code"]
        ):
            result.add_error(
                code="WRONG_ROUTING_MACHINE",
                message=(
                    f"Routing requires Machine "
                    f"{routing_machine_code}, "
                    f"but Production uses "
                    f"{data['machine_code']}."
                ),
                field="machine_code",
            )

        routing_machine_type = self._normalize_code(
            getattr(
                routing,
                "machine_type",
                "",
            )
        )

        machine_type = self._normalize_code(
            getattr(
                machine,
                "machine_type",
                "",
            )
        )

        if (
            routing_machine_type
            and machine_type
            and routing_machine_type != machine_type
        ):
            result.add_error(
                code="MACHINE_TYPE_MISMATCH",
                message=(
                    f"Routing requires Machine Type "
                    f"{routing_machine_type}, "
                    f"but Machine Master is "
                    f"{machine_type}."
                ),
                field="machine_code",
            )

    # ==========================================================
    # Duplicate validation
    # ==========================================================

    @staticmethod
    def _validate_duplicate(
        data,
        existing_record_hashes,
        result,
    ):
        normalized_hashes = {
            str(value or "").strip().lower()
            for value in existing_record_hashes
        }

        if data["record_hash"] in normalized_hashes:
            result.add_error(
                code="DUPLICATE_PRODUCTION_LOG",
                message=(
                    "Production Log already exists "
                    f"with hash {data['record_hash']}."
                ),
                field="record_hash",
            )

    # ==========================================================
    # Hash
    # ==========================================================

    @classmethod
    def build_record_hash(cls, data):
        start_time = data.get("start_time")
        finish_time = data.get("finish_time")

        parts = [
            cls._normalize_code(
                data.get("work_order_no")
            ),
            cls._normalize_code(
                data.get("product_code")
            ),
            cls._normalize_op(
                data.get("op_no")
            ),
            cls._normalize_code(
                data.get("machine_code")
            ),
            cls._normalize_code(
                data.get("employee_code")
            ),
            (
                start_time.isoformat()
                if isinstance(start_time, datetime)
                else str(start_time or "")
            ),
            (
                finish_time.isoformat()
                if isinstance(finish_time, datetime)
                else str(finish_time or "")
            ),
            str(data.get("ok_qty") or 0),
            str(data.get("ng_qty") or 0),
        ]

        raw_value = "|".join(parts)

        return sha256(
            raw_value.encode("utf-8")
        ).hexdigest()

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _normalize_text(value):
        if value is None:
            return ""

        text = str(value).strip()

        if text.lower() in {
            "nan",
            "none",
            "nat",
        }:
            return ""

        return " ".join(text.split())

    @classmethod
    def _normalize_code(cls, value):
        return cls._normalize_text(
            value
        ).upper()

    @classmethod
    def _normalize_op(cls, value):
        text = cls._normalize_code(value)

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
    def _normalize_shift(cls, value):
        text = cls._normalize_code(value)

        mapping = {
            "D": "DAY",
            "DAY": "DAY",
            "NGÀY": "DAY",
            "CA NGÀY": "DAY",
            "白班": "DAY",

            "N": "NIGHT",
            "NIGHT": "NIGHT",
            "ĐÊM": "NIGHT",
            "CA ĐÊM": "NIGHT",
            "夜班": "NIGHT",
        }

        return mapping.get(text, text)

    @staticmethod
    def _to_non_negative_int(value):
        try:
            number = int(float(value or 0))

        except (
            TypeError,
            ValueError,
        ):
            return 0

        return max(number, 0)

    @staticmethod
    def _to_non_negative_float(value):
        try:
            number = float(value or 0)

        except (
            TypeError,
            ValueError,
        ):
            return 0.0

        return max(number, 0.0)

    @staticmethod
    def _to_datetime(value):
        if value is None or value == "":
            return None

        if isinstance(value, datetime):
            return value

        try:
            return datetime.fromisoformat(
                str(value).strip()
            )

        except ValueError:
            return None