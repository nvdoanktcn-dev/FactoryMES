class PlanningError(Exception):
    """Lỗi cơ sở của Planning Engine."""


class InvalidCapacityInputError(PlanningError, ValueError):
    """Dữ liệu đầu vào tính công suất không hợp lệ."""


class InvalidRoutingError(PlanningError, ValueError):
    """Routing không đáp ứng các quy tắc nghiệp vụ."""