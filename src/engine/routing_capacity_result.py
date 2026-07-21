from dataclasses import dataclass


@dataclass(slots=True)
class RoutingCapacityItem:
    """
    Kết quả tính công suất của một công đoạn trong Routing.
    """

    # ==========================================================
    # Routing information
    # ==========================================================

    product_code: str
    op_no: str
    sequence: int

    machine_code: str
    machine_type: str

    cycle_time_sec: float

    # ==========================================================
    # Capacity
    # ==========================================================

    # Công suất của một máy trong một giờ
    capacity_per_hour: float

    # Số máy cần theo lý thuyết
    required_machine_count: float

    # Số máy thực tế cần bố trí, đã làm tròn lên
    required_machine_count_int: int

    # Công suất của OP so với OP chuẩn
    capacity_ratio: float

    # Chênh lệch công suất so với OP chuẩn
    capacity_gap_per_hour: float

    # ==========================================================
    # Machine availability
    # ==========================================================

    # Số máy hiện có cho công đoạn này
    available_machine_count: int = 0

    # ==========================================================
    # Bottleneck
    # ==========================================================

    is_bottleneck: bool = False

    # 1 là OP có công suất thấp nhất
    bottleneck_rank: int = 0

    # ==========================================================
    # Computed properties
    # ==========================================================

    @property
    def utilization_if_one_machine(self):
        """
        Tỷ lệ tải máy nếu chỉ bố trí một máy.

        Ví dụ:
            required_machine_count = 4
            -> một máy phải chịu tải 400%.
        """
        return self.required_machine_count * 100

    @property
    def machine_shortage(self):
        """
        Số máy còn thiếu để đáp ứng công suất yêu cầu.
        """
        return max(
            self.required_machine_count_int
            - self.available_machine_count,
            0,
        )

    @property
    def machine_surplus(self):
        """
        Số máy dư so với nhu cầu.
        """
        return max(
            self.available_machine_count
            - self.required_machine_count_int,
            0,
        )

    @property
    def has_machine_shortage(self):
        return self.machine_shortage > 0

    @property
    def capacity_status(self):
        """
        Trạng thái công suất để hiển thị trên Dashboard.
        """
        if self.is_bottleneck and self.has_machine_shortage:
            return "BOTTLENECK_SHORTAGE"

        if self.is_bottleneck:
            return "BOTTLENECK"

        if self.has_machine_shortage:
            return "MACHINE_SHORTAGE"

        return "BALANCED"