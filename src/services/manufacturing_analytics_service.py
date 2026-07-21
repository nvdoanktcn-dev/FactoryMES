from datetime import date, datetime

from src.database.session import get_session
from src.services.production_history_service import (
    ProductionHistoryService,
)


class ManufacturingAnalyticsService:
    """
    Service tổng hợp dữ liệu Manufacturing Analytics.

    Nguồn dữ liệu chính:
        ProductionLog
            ↓
        ProductionHistoryService
            ↓
        ManufacturingAnalyticsService
            ↓
        Dashboard / Report / API

    Service này không phụ thuộc UI.
    """

    def __init__(
        self,
        session=None,
        history_service=None,
    ):
        self.session = session or get_session()

        self.history_service = (
            history_service
            or ProductionHistoryService(
                self.session
            )
        )

    # ==========================================================
    # Public API
    # ==========================================================

    def build(
        self,
        start_date,
        end_date,
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
        Xây dựng toàn bộ Analytics cho khoảng thời gian.

        Returns:
            dict
        """
        start_date = self._normalize_date(
            start_date
        )

        end_date = self._normalize_date(
            end_date
        )

        if start_date is None:
            raise ValueError(
                "Start Date is required."
            )

        if end_date is None:
            raise ValueError(
                "End Date is required."
            )

        if end_date < start_date:
            raise ValueError(
                "End Date cannot be earlier "
                "than Start Date."
            )

        records = self.history_service.search(
            start_date=start_date,
            end_date=end_date,
            work_order_no=work_order_no,
            product_code=product_code,
            machine_code=machine_code,
            employee_code=employee_code,
            op_no=op_no,
            shift=shift,
            status=status,
            keyword=keyword,
        )

        summary = self._build_summary(
            records
        )

        machine = self._build_machine_analytics(
            records
        )

        employee = (
            self._build_employee_analytics(
                records
            )
        )

        product = self._build_product_analytics(
            records
        )

        work_order = (
            self._build_work_order_analytics(
                records
            )
        )

        daily = self._build_daily_analytics(
            records
        )

        ng = self._build_ng_analytics(
            records
        )

        oee = self._build_oee_analytics(
            records=records,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "day_count": (
                    end_date - start_date
                ).days + 1,
            },

            "summary": summary,

            "machine": machine,

            "employee": employee,

            "product": product,

            "work_order": work_order,

            "daily": daily,

            "ng": ng,

            "oee": oee,

            "filters": {
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

                "keyword":
                    str(
                        keyword or ""
                    ).strip(),
            },

            "record_count": len(records),

            # Giữ records để Report hoặc Export dùng lại.
            "records": records,
        }

    # ==========================================================
    # Summary
    # ==========================================================

    def _build_summary(self, records):
        base_summary = (
            self.history_service
            .build_summary(records)
        )

        runtime_sec = self._to_float(
            base_summary.get(
                "runtime_sec",
                0,
            )
        )

        downtime_min = self._to_float(
            base_summary.get(
                "downtime_min",
                0,
            )
        )

        downtime_sec = (
            downtime_min * 60
        )

        elapsed_sec = max(
            runtime_sec,
            0.0,
        )

        net_runtime_sec = max(
            elapsed_sec - downtime_sec,
            0.0,
        )

        availability_percent = (
            net_runtime_sec
            / elapsed_sec
            * 100
            if elapsed_sec > 0
            else 0.0
        )

        base_summary.update({
            "downtime_sec":
                downtime_sec,

            "net_runtime_sec":
                net_runtime_sec,

            "net_runtime_hour":
                net_runtime_sec / 3600,

            "availability_percent":
                min(
                    availability_percent,
                    100.0,
                ),

            "average_output_per_record": (
                base_summary["total_qty"]
                / base_summary["record_count"]
                if base_summary["record_count"]
                > 0
                else 0.0
            ),
        })

        return base_summary

    # ==========================================================
    # Machine Analytics
    # ==========================================================

    def _build_machine_analytics(
        self,
        records,
    ):
        grouped = (
            self.history_service
            .group_by_machine(records)
        )

        results = []

        for item in grouped:
            runtime_sec = self._to_float(
                item.get(
                    "runtime_sec",
                    0,
                )
            )

            downtime_min = self._to_float(
                item.get(
                    "downtime_min",
                    0,
                )
            )

            downtime_sec = (
                downtime_min * 60
            )

            net_runtime_sec = max(
                runtime_sec - downtime_sec,
                0.0,
            )

            availability = (
                net_runtime_sec
                / runtime_sec
                * 100
                if runtime_sec > 0
                else 0.0
            )

            machine_item = dict(item)

            machine_item.update({
                "downtime_sec":
                    downtime_sec,

                "net_runtime_sec":
                    net_runtime_sec,

                "net_runtime_hour":
                    net_runtime_sec / 3600,

                "availability_percent":
                    min(
                        availability,
                        100.0,
                    ),

                "utilization_percent":
                    min(
                        availability,
                        100.0,
                    ),

                "performance_percent":
                    self._estimate_performance(
                        item
                    ),

                "quality_percent":
                    self._to_float(
                        item.get(
                            "yield_percent",
                            0,
                        )
                    ),
            })

            machine_item["oee_percent"] = (
                machine_item[
                    "availability_percent"
                ]
                * machine_item[
                    "performance_percent"
                ]
                * machine_item[
                    "quality_percent"
                ]
                / 10000
            )

            results.append(
                machine_item
            )

        return sorted(
            results,
            key=lambda item: (
                item["ok_qty"],
                item["runtime_hour"],
            ),
            reverse=True,
        )

    # ==========================================================
    # Employee Analytics
    # ==========================================================

    def _build_employee_analytics(
        self,
        records,
    ):
        grouped = (
            self.history_service
            .group_by_employee(records)
        )

        results = []

        maximum_output_per_hour = max(
            (
                self._to_float(
                    item.get(
                        "output_per_hour",
                        0,
                    )
                )
                for item in grouped
            ),
            default=0.0,
        )

        for item in grouped:
            output_per_hour = self._to_float(
                item.get(
                    "output_per_hour",
                    0,
                )
            )

            relative_efficiency = (
                output_per_hour
                / maximum_output_per_hour
                * 100
                if maximum_output_per_hour > 0
                else 0.0
            )

            employee_item = dict(item)

            employee_item.update({
                "efficiency_percent":
                    min(
                        relative_efficiency,
                        100.0,
                    ),

                "quality_percent":
                    self._to_float(
                        item.get(
                            "yield_percent",
                            0,
                        )
                    ),

                "average_output_per_record": (
                    item["total_qty"]
                    / item["record_count"]
                    if item["record_count"] > 0
                    else 0.0
                ),
            })

            results.append(
                employee_item
            )

        return sorted(
            results,
            key=lambda item: (
                item["ok_qty"],
                item["efficiency_percent"],
            ),
            reverse=True,
        )

    # ==========================================================
    # Product Analytics
    # ==========================================================

    def _build_product_analytics(
        self,
        records,
    ):
        grouped = (
            self.history_service
            .group_by_product(records)
        )

        product_cycles = (
            self._calculate_actual_cycles(
                records,
                group_field="product_code",
            )
        )

        results = []

        for item in grouped:
            product_code = (
                self._normalize_code(
                    item.get(
                        "product_code",
                        "",
                    )
                )
            )

            product_item = dict(item)

            product_item.update({
                "actual_cycle_time_sec":
                    product_cycles.get(
                        product_code,
                        0.0,
                    ),

                "average_runtime_hour": (
                    item["runtime_hour"]
                    / item["record_count"]
                    if item["record_count"] > 0
                    else 0.0
                ),
            })

            results.append(
                product_item
            )

        return sorted(
            results,
            key=lambda item:
                item["total_qty"],
            reverse=True,
        )

    # ==========================================================
    # Work Order Analytics
    # ==========================================================

    def _build_work_order_analytics(
        self,
        records,
    ):
        grouped = (
            self.history_service
            .group_by_work_order(records)
        )

        work_order_master = (
            self._load_work_order_master()
        )

        results = []

        for item in grouped:
            work_order_no = (
                self._normalize_code(
                    item.get(
                        "work_order_no",
                        "",
                    )
                )
            )

            master = work_order_master.get(
                work_order_no
            )

            plan_qty = self._to_int(
                getattr(
                    master,
                    "plan_qty",
                    0,
                )
                if master is not None
                else 0
            )

            completed_qty = self._to_int(
                item.get(
                    "ok_qty",
                    0,
                )
            )

            remaining_qty = max(
                plan_qty - completed_qty,
                0,
            )

            progress_percent = (
                min(
                    completed_qty
                    / plan_qty
                    * 100,
                    100.0,
                )
                if plan_qty > 0
                else 0.0
            )

            work_order_item = dict(item)

            work_order_item.update({
                "plan_qty":
                    plan_qty,

                "completed_qty":
                    completed_qty,

                "remaining_qty":
                    remaining_qty,

                "progress_percent":
                    progress_percent,

                "status": (
                    getattr(
                        master,
                        "status",
                        "",
                    )
                    if master is not None
                    else ""
                ),

                "priority": (
                    getattr(
                        master,
                        "priority",
                        "",
                    )
                    if master is not None
                    else ""
                ),

                "start_date": (
                    getattr(
                        master,
                        "start_date",
                        None,
                    )
                    if master is not None
                    else None
                ),

                "due_date": (
                    getattr(
                        master,
                        "due_date",
                        None,
                    )
                    if master is not None
                    else None
                ),
            })

            results.append(
                work_order_item
            )

        return sorted(
            results,
            key=lambda item: (
                item["progress_percent"],
                item["ok_qty"],
            ),
            reverse=True,
        )

    # ==========================================================
    # Daily Analytics
    # ==========================================================

    def _build_daily_analytics(
        self,
        records,
    ):
        grouped = (
            self.history_service
            .group_by_date(records)
        )

        return [
            {
                **item,

                "production_date":
                    item["production_date"],

                "availability_percent":
                    self._calculate_availability(
                        runtime_sec=item[
                            "runtime_sec"
                        ],
                        downtime_min=item[
                            "downtime_min"
                        ],
                    ),
            }
            for item in grouped
        ]

    # ==========================================================
    # NG Analytics
    # ==========================================================

    def _build_ng_analytics(
        self,
        records,
    ):
        return {
            "by_product":
                self._sort_ng_group(
                    self.history_service
                    .group_by_product(records),
                    key_name="product_code",
                ),

            "by_machine":
                self._sort_ng_group(
                    self.history_service
                    .group_by_machine(records),
                    key_name="machine_code",
                ),

            "by_employee":
                self._sort_ng_group(
                    self.history_service
                    .group_by_employee(records),
                    key_name="employee_code",
                ),

            "by_reason":
                self._group_ng_by_reason(
                    records
                ),
        }

    @staticmethod
    def _sort_ng_group(
        items,
        key_name,
    ):
        results = [
            {
                key_name:
                    item.get(
                        key_name,
                        "",
                    ),

                "ng_qty":
                    item.get(
                        "ng_qty",
                        0,
                    ),

                "ng_percent":
                    item.get(
                        "ng_percent",
                        0.0,
                    ),

                "total_qty":
                    item.get(
                        "total_qty",
                        0,
                    ),

                "ok_qty":
                    item.get(
                        "ok_qty",
                        0,
                    ),
            }
            for item in items
        ]

        return sorted(
            results,
            key=lambda item: (
                item["ng_qty"],
                item["ng_percent"],
            ),
            reverse=True,
        )

    def _group_ng_by_reason(
        self,
        records,
    ):
        grouped = {}

        for record in records:
            reason = str(
                getattr(
                    record,
                    "downtime_reason",
                    "",
                )
                or "UNSPECIFIED"
            ).strip().upper()

            ng_qty = self._to_int(
                getattr(
                    record,
                    "ng_qty",
                    0,
                )
            )

            if ng_qty <= 0:
                continue

            grouped[reason] = (
                grouped.get(
                    reason,
                    0,
                )
                + ng_qty
            )

        total_ng = sum(
            grouped.values()
        )

        results = [
            {
                "reason": reason,

                "ng_qty": quantity,

                "ng_percent": (
                    quantity
                    / total_ng
                    * 100
                    if total_ng > 0
                    else 0.0
                ),
            }
            for reason, quantity
            in grouped.items()
        ]

        return sorted(
            results,
            key=lambda item:
                item["ng_qty"],
            reverse=True,
        )

    # ==========================================================
    # OEE Analytics
    # ==========================================================

    def _build_oee_analytics(
        self,
        records,
        start_date,
        end_date,
    ):
        """
        Ưu tiên OEEService nếu đã có.

        Nếu OEEService không chạy được, sử dụng
        phương án tổng hợp an toàn từ ProductionLog.
        """
        try:
            from src.services.oee_service import (
                OEEService,
            )

            oee_result = (
                OEEService(self.session)
                .calculate_range(
                    start_date=start_date,
                    end_date=end_date,
                )
            )

            summary = (
                oee_result.get(
                    "summary",
                    {}
                )
                if isinstance(
                    oee_result,
                    dict,
                )
                else {}
            )

            return {
                "overall":
                    self._to_float(
                        summary.get(
                            "oee_percent",
                            0,
                        )
                    ),

                "oee_percent":
                    self._to_float(
                        summary.get(
                            "oee_percent",
                            0,
                        )
                    ),

                "availability_percent":
                    self._to_float(
                        summary.get(
                            "availability_percent",
                            0,
                        )
                    ),

                "performance_percent":
                    self._to_float(
                        summary.get(
                            "performance_percent",
                            0,
                        )
                    ),

                "quality_percent":
                    self._to_float(
                        summary.get(
                            "quality_percent",
                            0,
                        )
                    ),

                "source":
                    "OEE_SERVICE",

                "errors":
                    oee_result.get(
                        "errors",
                        [],
                    ),
            }

        except Exception as error:
            fallback = (
                self._calculate_fallback_oee(
                    records
                )
            )

            fallback.update({
                "source":
                    "FALLBACK",

                "errors": [
                    str(error)
                ],
            })

            return fallback

    def _calculate_fallback_oee(
        self,
        records,
    ):
        summary = (
            self.history_service
            .build_summary(records)
        )

        runtime_sec = self._to_float(
            summary.get(
                "runtime_sec",
                0,
            )
        )

        downtime_sec = (
            self._to_float(
                summary.get(
                    "downtime_min",
                    0,
                )
            )
            * 60
        )

        net_runtime_sec = max(
            runtime_sec - downtime_sec,
            0,
        )

        availability = (
            net_runtime_sec
            / runtime_sec
            * 100
            if runtime_sec > 0
            else 0.0
        )

        quality = self._to_float(
            summary.get(
                "yield_percent",
                0,
            )
        )

        # Không có Routing Cycle Time đầy đủ thì
        # Performance chỉ là giá trị trung lập.
        performance = (
            100.0
            if summary.get(
                "total_qty",
                0,
            ) > 0
            else 0.0
        )

        oee = (
            availability
            * performance
            * quality
            / 10000
        )

        return {
            "overall": oee,
            "oee_percent": oee,
            "availability_percent":
                availability,
            "performance_percent":
                performance,
            "quality_percent":
                quality,
        }

    # ==========================================================
    # Work Order Master
    # ==========================================================

    def _load_work_order_master(self):
        try:
            from src.services.work_order_service import (
                WorkOrderService,
            )

            service = WorkOrderService()

            if hasattr(
                service,
                "get_all",
            ):
                work_orders = service.get_all()

            elif hasattr(
                service,
                "get_all_work_orders",
            ):
                work_orders = (
                    service
                    .get_all_work_orders()
                )

            elif hasattr(
                service,
                "search",
            ):
                work_orders = service.search("")

            else:
                return {}

            return {
                self._normalize_code(
                    work_order.work_order_no
                ): work_order

                for work_order in work_orders
            }

        except Exception:
            return {}

    # ==========================================================
    # Helper calculations
    # ==========================================================

    def _calculate_actual_cycles(
        self,
        records,
        group_field,
    ):
        grouped = {}

        for record in records:
            key = self._normalize_code(
                getattr(
                    record,
                    group_field,
                    "",
                )
            )

            if not key:
                continue

            runtime_sec = self._to_float(
                getattr(
                    record,
                    "run_time_sec",
                    0,
                )
            )

            total_qty = (
                self._to_int(
                    getattr(
                        record,
                        "ok_qty",
                        0,
                    )
                )
                + self._to_int(
                    getattr(
                        record,
                        "ng_qty",
                        0,
                    )
                )
            )

            bucket = grouped.setdefault(
                key,
                {
                    "runtime_sec": 0.0,
                    "total_qty": 0,
                },
            )

            bucket[
                "runtime_sec"
            ] += runtime_sec

            bucket[
                "total_qty"
            ] += total_qty

        return {
            key: (
                values["runtime_sec"]
                / values["total_qty"]
                if values["total_qty"] > 0
                else 0.0
            )

            for key, values
            in grouped.items()
        }

    @staticmethod
    def _calculate_availability(
        runtime_sec,
        downtime_min,
    ):
        runtime_sec = float(
            runtime_sec or 0
        )

        downtime_sec = float(
            downtime_min or 0
        ) * 60

        if runtime_sec <= 0:
            return 0.0

        return min(
            max(
                runtime_sec - downtime_sec,
                0.0,
            )
            / runtime_sec
            * 100,
            100.0,
        )

    @staticmethod
    def _estimate_performance(
        summary,
    ):
        """
        Khi chưa có Cycle Time theo từng log,
        dùng mức độ Output/Hour tương đối.

        OEE chính xác vẫn ưu tiên OEEService.
        """
        output_per_hour = float(
            summary.get(
                "output_per_hour",
                0,
            )
            or 0
        )

        if output_per_hour <= 0:
            return 0.0

        return 100.0

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