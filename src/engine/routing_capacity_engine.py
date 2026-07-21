import math
from collections import Counter

from src.engine.routing_capacity_result import (
    RoutingCapacityItem,
)


class RoutingCapacityEngine:
    """
    Engine tính công suất Routing.

    Chức năng:
    - Tính công suất mỗi OP.
    - Xác định bottleneck.
    - Tính số máy lý thuyết cần bố trí.
    - Làm tròn số máy thực tế cần dùng.
    - So sánh số máy cần với số máy hiện có.
    - Xếp hạng bottleneck.

    Engine không truy cập database.
    """

    def calculate(
        self,
        routing_list,
        available_machine_counts=None,
        reference_mode="FIRST_OPERATION",
    ):
        """
        Args:
            routing_list:
                Danh sách Routing model hoặc object có các thuộc tính:

                    product_code
                    op_no
                    sequence
                    machine_code
                    machine_type
                    cycle_time_sec

            available_machine_counts:
                Dictionary số máy hiện có.

                Hỗ trợ hai cách truyền:

                    Theo Machine Type:
                    {
                        "CNC": 10,
                        "ROBOT": 5,
                    }

                    Theo Machine Code:
                    {
                        "BL01": 1,
                        "BL02": 1,
                        "BR01": 2,
                    }

            reference_mode:
                FIRST_OPERATION:
                    Dùng công suất OP đầu làm mục tiêu.

                MAX_CAPACITY:
                    Dùng OP có công suất cao nhất làm mục tiêu.

        Returns:
            list[RoutingCapacityItem]
        """
        if not routing_list:
            return []

        available_machine_counts = (
            available_machine_counts or {}
        )

        normalized_routings = self._prepare_routings(
            routing_list
        )

        reference_capacity = (
            self._resolve_reference_capacity(
                normalized_routings,
                reference_mode,
            )
        )

        capacity_items = []

        for routing in normalized_routings:
            cycle_time_sec = self._to_positive_float(
                getattr(
                    routing,
                    "cycle_time_sec",
                    0,
                ),
                field_name=(
                    f"Cycle Time "
                    f"{getattr(routing, 'op_no', '')}"
                ),
            )

            capacity_per_hour = (
                3600.0 / cycle_time_sec
            )

            required_machine_count = (
                reference_capacity
                / capacity_per_hour
            )

            required_machine_count_int = (
                max(
                    math.ceil(
                        required_machine_count
                    ),
                    1,
                )
            )

            capacity_ratio = (
                capacity_per_hour
                / reference_capacity
                * 100
                if reference_capacity > 0
                else 0.0
            )

            capacity_gap_per_hour = (
                reference_capacity
                - capacity_per_hour
            )

            machine_code = self._normalize_code(
                getattr(
                    routing,
                    "machine_code",
                    "",
                )
            )

            machine_type = self._normalize_code(
                getattr(
                    routing,
                    "machine_type",
                    "",
                )
            )

            available_machine_count = (
                self._resolve_available_machine_count(
                    machine_code=machine_code,
                    machine_type=machine_type,
                    available_machine_counts=(
                        available_machine_counts
                    ),
                )
            )

            capacity_items.append(
                RoutingCapacityItem(
                    product_code=(
                        self._normalize_code(
                            getattr(
                                routing,
                                "product_code",
                                "",
                            )
                        )
                    ),
                    op_no=self._normalize_op(
                        getattr(
                            routing,
                            "op_no",
                            "",
                        )
                    ),
                    sequence=self._to_positive_int(
                        getattr(
                            routing,
                            "sequence",
                            0,
                        ),
                        field_name="Sequence",
                    ),
                    machine_code=machine_code,
                    machine_type=machine_type,
                    cycle_time_sec=cycle_time_sec,
                    capacity_per_hour=(
                        capacity_per_hour
                    ),
                    required_machine_count=(
                        required_machine_count
                    ),
                    required_machine_count_int=(
                        required_machine_count_int
                    ),
                    capacity_ratio=capacity_ratio,
                    capacity_gap_per_hour=(
                        capacity_gap_per_hour
                    ),
                    available_machine_count=(
                        available_machine_count
                    ),
                )
            )

        self._assign_bottleneck_ranking(
            capacity_items
        )

        return capacity_items

    def calculate_summary(
        self,
        routing_list,
        available_machine_counts=None,
        reference_mode="FIRST_OPERATION",
    ):
        """
        Trả về kết quả tổng hợp toàn bộ Routing.
        """
        items = self.calculate(
            routing_list=routing_list,
            available_machine_counts=(
                available_machine_counts
            ),
            reference_mode=reference_mode,
        )

        if not items:
            return {
                "product_code": "",
                "operation_count": 0,
                "reference_capacity_per_hour": 0.0,
                "line_capacity_per_hour": 0.0,
                "bottleneck_op": "",
                "bottleneck_capacity_per_hour": 0.0,
                "total_required_machine_count": 0,
                "total_available_machine_count": 0,
                "total_machine_shortage": 0,
                "has_machine_shortage": False,
                "items": [],
            }

        bottleneck = min(
            items,
            key=lambda item:
                item.capacity_per_hour,
        )

        return {
            "product_code":
                items[0].product_code,

            "operation_count":
                len(items),

            "reference_capacity_per_hour":
                max(
                    item.capacity_per_hour
                    * item.required_machine_count
                    for item in items
                ),

            # Công suất toàn Routing bị giới hạn
            # bởi OP chậm nhất khi chỉ có một máy/OP.
            "line_capacity_per_hour":
                bottleneck.capacity_per_hour,

            "bottleneck_op":
                bottleneck.op_no,

            "bottleneck_capacity_per_hour":
                bottleneck.capacity_per_hour,

            "total_required_machine_count":
                sum(
                    item.required_machine_count_int
                    for item in items
                ),

            "total_available_machine_count":
                sum(
                    item.available_machine_count
                    for item in items
                ),

            "total_machine_shortage":
                sum(
                    item.machine_shortage
                    for item in items
                ),

            "has_machine_shortage":
                any(
                    item.has_machine_shortage
                    for item in items
                ),

            "items":
                items,
        }

    # ==========================================================
    # Routing preparation
    # ==========================================================

    def _prepare_routings(
        self,
        routing_list,
    ):
        normalized = []

        seen_ops = set()
        seen_sequences = set()

        for routing in routing_list:
            product_code = self._normalize_code(
                getattr(
                    routing,
                    "product_code",
                    "",
                )
            )

            op_no = self._normalize_op(
                getattr(
                    routing,
                    "op_no",
                    "",
                )
            )

            sequence = self._to_positive_int(
                getattr(
                    routing,
                    "sequence",
                    0,
                ),
                field_name="Sequence",
            )

            cycle_time = self._to_positive_float(
                getattr(
                    routing,
                    "cycle_time_sec",
                    0,
                ),
                field_name=(
                    f"Cycle Time {op_no}"
                ),
            )

            if not product_code:
                raise ValueError(
                    "Product Code is required."
                )

            if not op_no:
                raise ValueError(
                    "OP No is required."
                )

            op_key = (
                product_code,
                op_no,
            )

            sequence_key = (
                product_code,
                sequence,
            )

            if op_key in seen_ops:
                raise ValueError(
                    "Duplicate Routing OP: "
                    f"{product_code} - {op_no}"
                )

            if sequence_key in seen_sequences:
                raise ValueError(
                    "Duplicate Routing Sequence: "
                    f"{product_code} - {sequence}"
                )

            seen_ops.add(op_key)
            seen_sequences.add(sequence_key)

            # Chỉ nhằm xác nhận cycle time hợp lệ.
            _ = cycle_time

            normalized.append(routing)

        products = {
            self._normalize_code(
                getattr(
                    routing,
                    "product_code",
                    "",
                )
            )
            for routing in normalized
        }

        if len(products) > 1:
            raise ValueError(
                "Routing Capacity Engine only accepts "
                "one Product per calculation."
            )

        return sorted(
            normalized,
            key=lambda item: (
                int(
                    getattr(
                        item,
                        "sequence",
                        0,
                    )
                    or 0
                ),
                self._normalize_op(
                    getattr(
                        item,
                        "op_no",
                        "",
                    )
                ),
            ),
        )

    # ==========================================================
    # Reference capacity
    # ==========================================================

    def _resolve_reference_capacity(
        self,
        routing_list,
        reference_mode,
    ):
        capacities = [
            3600.0
            / self._to_positive_float(
                getattr(
                    routing,
                    "cycle_time_sec",
                    0,
                ),
                field_name="Cycle Time",
            )
            for routing in routing_list
        ]

        mode = str(
            reference_mode
            or "FIRST_OPERATION"
        ).strip().upper()

        if mode == "FIRST_OPERATION":
            return capacities[0]

        if mode == "MAX_CAPACITY":
            return max(capacities)

        raise ValueError(
            f"Unsupported reference mode: "
            f"{reference_mode}"
        )

    # ==========================================================
    # Bottleneck
    # ==========================================================

    @staticmethod
    def _assign_bottleneck_ranking(
        capacity_items,
    ):
        """
        Xếp hạng theo công suất tăng dần.

        Các OP có cùng công suất sẽ cùng hạng.
        """
        unique_capacities = sorted({
            round(
                item.capacity_per_hour,
                10,
            )
            for item in capacity_items
        })

        rank_by_capacity = {
            capacity: rank
            for rank, capacity in enumerate(
                unique_capacities,
                start=1,
            )
        }

        minimum_capacity = min(
            unique_capacities
        )

        for item in capacity_items:
            rounded_capacity = round(
                item.capacity_per_hour,
                10,
            )

            item.bottleneck_rank = (
                rank_by_capacity[
                    rounded_capacity
                ]
            )

            item.is_bottleneck = (
                rounded_capacity
                == minimum_capacity
            )

    # ==========================================================
    # Machine availability
    # ==========================================================

    @classmethod
    def _resolve_available_machine_count(
        cls,
        machine_code,
        machine_type,
        available_machine_counts,
    ):
        normalized_counts = {
            cls._normalize_code(key):
                cls._to_non_negative_int(value)
            for key, value
            in available_machine_counts.items()
        }

        if (
            machine_code
            and machine_code in normalized_counts
        ):
            return normalized_counts[
                machine_code
            ]

        if (
            machine_type
            and machine_type in normalized_counts
        ):
            return normalized_counts[
                machine_type
            ]

        return 0

    @classmethod
    def count_available_machines(
        cls,
        machines,
    ):
        """
        Tạo dictionary số máy hiện có theo Machine Type.

        Ví dụ kết quả:

            {
                "CNC": 12,
                "ROBOT": 6,
            }

        Chỉ tính máy không ở trạng thái INACTIVE.
        """
        machine_types = []

        for machine in machines or []:
            status = cls._normalize_code(
                getattr(
                    machine,
                    "status",
                    "",
                )
            )

            if status in {
                "INACTIVE",
                "DISABLED",
                "RETIRED",
            }:
                continue

            machine_type = cls._normalize_code(
                getattr(
                    machine,
                    "machine_type",
                    "",
                )
            )

            if machine_type:
                machine_types.append(
                    machine_type
                )

        return dict(
            Counter(machine_types)
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

    @staticmethod
    def _to_positive_float(
        value,
        field_name="Value",
    ):
        try:
            number = float(value)

        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"{field_name} must be numeric: "
                f"{value}"
            ) from error

        if number <= 0:
            raise ValueError(
                f"{field_name} must be greater "
                "than zero."
            )

        return number

    @staticmethod
    def _to_positive_int(
        value,
        field_name="Value",
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
                f"{field_name} must be an integer: "
                f"{value}"
            ) from error

        if number <= 0:
            raise ValueError(
                f"{field_name} must be greater "
                "than zero."
            )

        return number

    @staticmethod
    def _to_non_negative_int(value):
        try:
            number = int(
                float(value or 0)
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0

        return max(
            number,
            0,
        )