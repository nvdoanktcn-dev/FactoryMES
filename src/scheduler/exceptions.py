class SchedulerError(Exception):
    """Lỗi cơ sở của module Scheduler."""


class InvalidScheduleInputError(SchedulerError):
    """Dữ liệu đầu vào của Scheduler không hợp lệ."""


class InvalidBookingError(SchedulerError):
    """Thông tin đặt lịch máy không hợp lệ."""


class InsufficientResourceError(SchedulerError):
    """Không đủ tài nguyên máy để lập lịch."""


class MachineUnavailableError(SchedulerError):
    """Máy không khả dụng trong khoảng thời gian yêu cầu."""