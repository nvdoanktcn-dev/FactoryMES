class ExecutionError(Exception):
    """Base exception của Execution layer."""


class InvalidExecutionTaskError(ExecutionError):
    """ExecutionTask không hợp lệ."""


class InvalidTaskTransitionError(ExecutionError):
    """Chuyển trạng thái task không hợp lệ."""


class InvalidProductionQuantityError(ExecutionError):
    """Số lượng sản xuất không hợp lệ."""


class TaskAlreadyFinishedError(ExecutionError):
    """Task đã hoàn thành."""


# ===== Tracker =====

class DuplicateExecutionTaskError(ExecutionError):
    """ExecutionTask đã tồn tại."""


class ExecutionTaskNotFoundError(ExecutionError):
    """Không tìm thấy ExecutionTask."""
    

class InvalidDowntimeEventError(ExecutionError):
    """DowntimeEvent không hợp lệ."""


class DuplicateDowntimeEventError(ExecutionError):
    """DowntimeEvent đã tồn tại trong tracker."""


class DowntimeEventNotFoundError(ExecutionError):
    """Không tìm thấy DowntimeEvent."""

class InvalidMachineStateError(ExecutionError):
    """Trạng thái máy không hợp lệ."""


class DuplicateMachineError(ExecutionError):
    """Máy đã tồn tại trong MachineStateTracker."""


class MachineNotFoundError(ExecutionError):
    """Không tìm thấy máy trong MachineStateTracker."""


class InvalidMachineTransitionError(ExecutionError):
    """Chuyển trạng thái máy không hợp lệ."""
    

class ExecutionCoordinatorError(ExecutionError):
    """Lỗi điều phối Execution."""


class MachineBusyError(ExecutionCoordinatorError):
    """Máy đang được một task khác sử dụng."""


class MachineDowntimeError(ExecutionCoordinatorError):
    """Máy đang downtime nên không thể chạy task."""


class TaskMachineMismatchError(ExecutionCoordinatorError):
    """Task và máy được chỉ định không khớp."""