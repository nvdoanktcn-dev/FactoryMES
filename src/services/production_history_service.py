from datetime import date, datetime, time, timedelta

from src.database.session import get_session
from src.repository.production_log_repository import (
    ProductionLogRepository,
)


class ProductionHistoryService:
    """
    Service đọc và tổng hợp lịch sử sản xuất.

    Chức năng:
    - Lọc theo khoảng ngày
    - Work Order
    - Product
    - Machine
    - Employee
    - OP
    - Shift
    - Status
    - Tính tổng OK, NG, Runtime, Downtime, Yield
    - Tổng hợp theo Machine, Employee, Product, Work Order
    """

    def __init__(self, session=None):
        self.session = session or get_session()

        self.repository = ProductionLogRepository(
            self.session
        )

    # ==========================================================
    # Query
    # ==========================================================

    def search(
        self,
        start_date=None,
        end_date=None,
        work_order_no=None,
        product_code=None,
        machine_code=None,
        employee_code=None,
        op_no=None,
        shift=None,
        status=None,
        keyword=None,
    ):
        """
        Trả về danh sách Production Log đã lọc.
        """
        records = self._load_records(
            start_date=start_date,
            end_date=end_date,
        )

        normalized_filters = {
            "work_order_no":
                self._normalize_code(
                    work_order_no
                ),

            "product_code":
                self._normalize_code(
                    product_code
                ),

            "machine_code":
                self._normalize_code(
                    machine_code
                ),

            "employee_code":
                self._normalize_code(
                    employee_code
                ),

            "op_no":
                self._normalize_op(
                    op_no
                ),

            "shift":
                self._normalize_code(
                    shift
                ),

            "status":
                self._normalize_code(
                    status
                ),
        }

        keyword = str(
            keyword or ""
        ).strip().lower()

        filtered = []

        for record in records:
            if not self._matches_filters(
                record,
                normalized_filters,
            ):
                continue

            if (
                keyword
                and not self._matches_keyword(
                    record,
                    keyword,
                )
            ):
                continue

            filtered.append(record)

        return sorted(
            filtered,
            key=lambda item: (
                self._datetime_sort_value(
                    getattr(
                        item,
                        "start_time",
                        None,
                    )
                ),
                self._to_int(
                    getattr(
                        item,
                        "id",
                        0,
                    )
                ),
            ),
            reverse=True,
        )

    def get_by_id(self, production_log_id):
        production_log_id = self._to_int(
            production_log_id
        )

        if production_log_id <= 0:
            raise ValueError(
                "Production Log ID must be greater "
                "than zero."
            )

        if hasattr(
            self.repository,
            "get_by_id",
        ):
            return self.repository.get_by_id(
                production_log_id
            )

        records = self.repository.get_all()

        return next(
            (
                record
                for record in records
                if self._to_int(
                    getattr(
                        record,
                        "id",
                        0,
                    )
                )
                == production_log_id
            ),
            None,
        )

    # ==========================================================
    # Summary
    # ==========================================================

    def build_summary(self, records):
        records = list(records or [])

        runtime_sec = sum(
            self._to_float(
                getattr(
                    record,
                    "run_time_sec",
                    0,
                )
            )
            for record in records
        )

        downtime_min = sum(
            self._to_float(
                getattr(
                    record,
                    "downtime_min",
                    0,
                )
            )
            for record in records
        )

        ok_qty = sum(
            self._to_int(
                getattr(
                    record,
                    "ok_qty",
                    0,
                )
            )
            for record in records
        )

        ng_qty = sum(
            self._to_int(
                getattr(
                    record,
                    "ng_qty",
                    0,
                )
            )
            for record in records
        )

        total_qty = ok_qty + ng_qty

        yield_percent = (
            ok_qty / total_qty * 100
            if total_qty > 0
            else 0.0
        )

        ng_percent = (
            ng_qty / total_qty * 100
            if total_qty > 0
            else 0.0
        )

        machine_codes = {
            self._normalize_code(
                getattr(
                    record,
                    "machine_code",
                    "",
                )
            )
            for record in records
            if self._normalize_code(
                getattr(
                    record,
                    "machine_code",
                    "",
                )
            )
        }

        employee_codes = {
            self._normalize_code(
                getattr(
                    record,
                    "employee_code",
                    "",
                )
            )
            for record in records
            if self._normalize_code(
                getattr(
                    record,
                    "employee_code",
                    "",
                )
            )
        }

        work_orders = {
            self._normalize_code(
                getattr(
                    record,
                    "work_order_no",
                    "",
                )
            )
            for record in records
            if self._normalize_code(
                getattr(
                    record,
                    "work_order_no",
                    "",
                )
            )
        }

        return {
            "record_count": len(records),
            "work_order_count": len(work_orders),
            "machine_count": len(machine_codes),
            "employee_count": len(employee_codes),

            "runtime_sec": runtime_sec,
            "runtime_hour": runtime_sec / 3600,

            "downtime_min": downtime_min,
            "downtime_hour": downtime_min / 60,

            "ok_qty": ok_qty,
            "ng_qty": ng_qty,
            "total_qty": total_qty,

            "yield_percent": yield_percent,
            "ng_percent": ng_percent,

            "output_per_hour": (
                total_qty * 3600 / runtime_sec
                if runtime_sec > 0
                else 0.0
            ),
        }

    # ==========================================================
    # Grouping
    # ==========================================================

    def group_by_machine(self, records):
        return self._group_records(
            records=records,
            key_getter=lambda record:
                self._normalize_code(
                    getattr(
                        record,
                        "machine_code",
                        "",
                    )
                ),
            key_name="machine_code",
        )

    def group_by_employee(self, records):
        return self._group_records(
            records=records,
            key_getter=lambda record:
                self._normalize_code(
                    getattr(
                        record,
                        "employee_code",
                        "",
                    )
                ),
            key_name="employee_code",
        )

    def group_by_product(self, records):
        return self._group_records(
            records=records,
            key_getter=lambda record:
                self._normalize_code(
                    getattr(
                        record,
                        "product_code",
                        "",
                    )
                ),
            key_name="product_code",
        )

    def group_by_work_order(self, records):
        return self._group_records(
            records=records,
            key_getter=lambda record:
                self._normalize_code(
                    getattr(
                        record,
                        "work_order_no",
                        "",
                    )
                ),
            key_name="work_order_no",
        )

    def group_by_date(self, records):
        grouped = {}

        for record in records or []:
            start_time = getattr(
                record,
                "start_time",
                None,
            )

            if isinstance(start_time, datetime):
                group_key = start_time.date()

            elif isinstance(start_time, date):
                group_key = start_time

            else:
                continue

            grouped.setdefault(
                group_key,
                [],
            ).append(record)

        results = []

        for group_date, group_records in grouped.items():
            summary = self.build_summary(
                group_records
            )

            summary[
                "production_date"
            ] = group_date

            results.append(summary)

        return sorted(
            results,
            key=lambda item:
                item["production_date"],
        )

    # ==========================================================
    # Ranking
    # ==========================================================

    def get_top_ng_products(
        self,
        records,
        limit=10,
    ):
        results = self.group_by_product(
            records
        )

        return sorted(
            results,
            key=lambda item: (
                item["ng_qty"],
                item["ng_percent"],
            ),
            reverse=True,
        )[:limit]

    def get_top_machine_output(
        self,
        records,
        limit=10,
    ):
        results = self.group_by_machine(
            records
        )

        return sorted(
            results,
            key=lambda item:
                item["ok_qty"],
            reverse=True,
        )[:limit]

    def get_top_employee_output(
        self,
        records,
        limit=10,
    ):
        results = self.group_by_employee(
            records
        )

        return sorted(
            results,
            key=lambda item:
                item["ok_qty"],
            reverse=True,
        )[:limit]

    # ==========================================================
    # Internal query
    # ==========================================================

    def _load_records(
        self,
        start_date=None,
        end_date=None,
    ):
        normalized_start = self._normalize_date(
            start_date
        )

        normalized_end = self._normalize_date(
            end_date
        )

        if (
            normalized_start is not None
            and normalized_end is not None
            and normalized_end < normalized_start
        ):
            raise ValueError(
                "End Date cannot be earlier "
                "than Start Date."
            )

        if (
            normalized_start is not None
            and normalized_end is not None
            and hasattr(
                self.repository,
                "get_by_date_range",
            )
        ):
            return (
                self.repository
                .get_by_date_range(
                    normalized_start,
                    normalized_end,
                )
            )

        records = self.repository.get_all()

        if (
            normalized_start is None
            and normalized_end is None
        ):
            return records

        filtered = []

        for record in records:
            start_time = getattr(
                record,
                "start_time",
                None,
            )

            record_date = (
                start_time.date()
                if isinstance(
                    start_time,
                    datetime,
                )
                else start_time
                if isinstance(
                    start_time,
                    date,
                )
                else None
            )

            if record_date is None:
                continue

            if (
                normalized_start is not None
                and record_date
                < normalized_start
            ):
                continue

            if (
                normalized_end is not None
                and record_date
                > normalized_end
            ):
                continue

            filtered.append(record)

        return filtered

    # ==========================================================
    # Group helper
    # ==========================================================

    def _group_records(
        self,
        records,
        key_getter,
        key_name,
    ):
        grouped = {}

        for record in records or []:
            group_key = key_getter(record)

            if not group_key:
                continue

            grouped.setdefault(
                group_key,
                [],
            ).append(record)

        results = []

        for group_key, group_records in grouped.items():
            summary = self.build_summary(
                group_records
            )

            summary[key_name] = group_key

            results.append(summary)

        return sorted(
            results,
            key=lambda item:
                str(item[key_name]),
        )

    # ==========================================================
    # Filter helpers
    # ==========================================================

    def _matches_filters(
        self,
        record,
        filters,
    ):
        comparisons = {
            "work_order_no":
                self._normalize_code(
                    getattr(
                        record,
                        "work_order_no",
                        "",
                    )
                ),

            "product_code":
                self._normalize_code(
                    getattr(
                        record,
                        "product_code",
                        "",
                    )
                ),

            "machine_code":
                self._normalize_code(
                    getattr(
                        record,
                        "machine_code",
                        "",
                    )
                ),

            "employee_code":
                self._normalize_code(
                    getattr(
                        record,
                        "employee_code",
                        "",
                    )
                ),

            "op_no":
                self._normalize_op(
                    getattr(
                        record,
                        "op_no",
                        "",
                    )
                ),

            "shift":
                self._normalize_code(
                    getattr(
                        record,
                        "shift",
                        "",
                    )
                ),

            "status":
                self._normalize_code(
                    getattr(
                        record,
                        "status",
                        "",
                    )
                ),
        }

        for field_name, expected_value in filters.items():
            if not expected_value:
                continue

            if (
                comparisons[field_name]
                != expected_value
            ):
                return False

        return True

    @staticmethod
    def _matches_keyword(
        record,
        keyword,
    ):
        fields = [
            "work_order_no",
            "product_code",
            "op_no",
            "machine_code",
            "employee_code",
            "shift",
            "status",
            "downtime_reason",
            "remark",
        ]

        return any(
            keyword
            in str(
                getattr(
                    record,
                    field_name,
                    "",
                )
                or ""
            ).lower()
            for field_name in fields
        )

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _normalize_code(value):
        return str(
            value or ""
        ).strip().upper()

    @classmethod
    def _normalize_op(cls, value):
        text = cls._normalize_code(
            value
        )

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

    @staticmethod
    def _normalize_date(value):
        if value is None or value == "":
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        try:
            return datetime.fromisoformat(
                str(value).strip()
            ).date()

        except ValueError as error:
            raise ValueError(
                f"Invalid Date: {value}"
            ) from error

    @staticmethod
    def _to_int(value):
        try:
            return int(
                float(value or 0)
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0

    @staticmethod
    def _to_float(value):
        try:
            return float(
                value or 0
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    @staticmethod
    def _datetime_sort_value(value):
        if isinstance(value, datetime):
            return value

        try:
            return datetime.fromisoformat(
                str(value)
            )

        except (
            TypeError,
            ValueError,
        ):
            return datetime.min