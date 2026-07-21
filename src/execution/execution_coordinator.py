from __future__ import annotations

from datetime import datetime

from src.execution.downtime import DowntimeEvent
from src.execution.downtime_tracker import DowntimeTracker
from src.execution.exceptions import (
    ExecutionCoordinatorError,
    MachineBusyError,
    MachineDowntimeError,
)
from src.execution.execution_engine import ExecutionEngine
from src.execution.machine_state import MachineState
from src.execution.machine_state_tracker import (
    MachineStateChange,
    MachineStateTracker,
)
from src.execution.models import (
    ExecutionTask,
    TaskStatus,
)
from src.execution.tracker import ExecutionTracker


class ExecutionCoordinator:
    """
    Điều phối ExecutionTask, trạng thái máy và downtime.

    Coordinator không thay thế các engine/tracker hiện có.
    Nó gọi các module đó theo đúng thứ tự và giữ trạng thái
    giữa các module được đồng bộ.
    """

    def __init__(
        self,
        *,
        execution_engine: ExecutionEngine | None = None,
        execution_tracker: ExecutionTracker | None = None,
        machine_state_tracker: MachineStateTracker | None = None,
        downtime_tracker: DowntimeTracker | None = None,
    ) -> None:
        self.execution_engine = (
            execution_engine
            if execution_engine is not None
            else ExecutionEngine()
        )
        self.execution_tracker = (
            execution_tracker
            if execution_tracker is not None
            else ExecutionTracker()
        )
        self.machine_state_tracker = (
            machine_state_tracker
            if machine_state_tracker is not None
            else MachineStateTracker()
        )
        self.downtime_tracker = (
            downtime_tracker
            if downtime_tracker is not None
            else DowntimeTracker()
        )

    def register_task(
        self,
        task: ExecutionTask,
    ) -> ExecutionTask:
        """
        Đăng ký task và máy tương ứng.

        Máy mới được đăng ký ở trạng thái IDLE.
        Nếu máy đã tồn tại thì giữ nguyên trạng thái hiện tại.
        """
        self._validate_task(task)

        machine_code = task.machine_code

        if machine_code not in self.machine_state_tracker:
            self.machine_state_tracker.register(
                machine_code,
                MachineState.IDLE,
            )

        self._ensure_machine_can_accept_task(task)

        self.execution_tracker.add(task)

        return task

    def ready_task(
        self,
        task: ExecutionTask,
    ) -> ExecutionTask:
        self._require_registered_task(task)

        self.execution_engine.ready(task)

        return task

    def start_task(
        self,
        task: ExecutionTask,
    ) -> ExecutionTask:
        """
        Đưa task sang RUNNING và đồng bộ máy sang RUNNING.

        Nếu task còn WAITING, Coordinator tự động gọi ready().
        """
        self._require_registered_task(task)
        self._ensure_machine_can_start(task)

        if task.status is TaskStatus.WAITING:
            self.execution_engine.ready(task)

        self.execution_engine.start(task)

        self._transition_machine_if_needed(
            task.machine_code,
            MachineState.RUNNING,
            reason=(
                f"Started task {task.work_order_code} "
                f"{task.op_code}"
            ),
        )

        return task

    def pause_task(
        self,
        task: ExecutionTask,
    ) -> ExecutionTask:
        self._require_registered_task(task)

        self.execution_engine.pause(task)

        self._transition_machine_if_needed(
            task.machine_code,
            MachineState.PAUSED,
            reason=(
                f"Paused task {task.work_order_code} "
                f"{task.op_code}"
            ),
        )

        return task

    def resume_task(
        self,
        task: ExecutionTask,
    ) -> ExecutionTask:
        self._require_registered_task(task)
        self._ensure_machine_not_in_downtime(
            task.machine_code
        )

        self.execution_engine.resume(task)

        self._transition_machine_if_needed(
            task.machine_code,
            MachineState.RUNNING,
            reason=(
                f"Resumed task {task.work_order_code} "
                f"{task.op_code}"
            ),
        )

        return task

    def finish_task(
        self,
        task: ExecutionTask,
    ) -> ExecutionTask:
        self._require_registered_task(task)

        self.execution_engine.finish(task)

        self._set_machine_idle_if_possible(
            task.machine_code,
            reason=(
                f"Finished task {task.work_order_code} "
                f"{task.op_code}"
            ),
        )

        return task

    def cancel_task(
        self,
        task: ExecutionTask,
    ) -> ExecutionTask:
        self._require_registered_task(task)

        self.execution_engine.cancel(task)

        self._set_machine_idle_if_possible(
            task.machine_code,
            reason=(
                f"Cancelled task {task.work_order_code} "
                f"{task.op_code}"
            ),
        )

        return task

    def record_production(
        self,
        task: ExecutionTask,
        *,
        ok_qty: int = 0,
        ng_qty: int = 0,
    ) -> ExecutionTask:
        """
        Ghi nhận sản lượng.

        Nếu ExecutionEngine tự động hoàn thành task khi đủ kế hoạch,
        Coordinator cũng tự động đưa máy về IDLE.
        """
        self._require_registered_task(task)

        self.execution_engine.record_production(
            task,
            ok_qty=ok_qty,
            ng_qty=ng_qty,
        )

        if task.status is TaskStatus.FINISHED:
            self._set_machine_idle_if_possible(
                task.machine_code,
                reason=(
                    f"Task auto-finished after production: "
                    f"{task.work_order_code} {task.op_code}"
                ),
            )

        return task

    def add_downtime(
        self,
        event: DowntimeEvent,
    ) -> DowntimeEvent:
        """
        Thêm downtime và chuyển máy sang DOWNTIME.

        Nếu máy chưa được đăng ký, máy được tạo ở trạng thái IDLE
        trước khi chuyển sang DOWNTIME.
        """
        if not isinstance(event, DowntimeEvent):
            raise ExecutionCoordinatorError(
                "event must be a DowntimeEvent instance."
            )

        machine_code = event.machine_code

        if machine_code not in self.machine_state_tracker:
            self.machine_state_tracker.register(
                machine_code,
                MachineState.IDLE,
            )

        self.downtime_tracker.add(event)

        try:
            self._transition_machine_if_needed(
                machine_code,
                MachineState.DOWNTIME,
                reason=(
                    f"Downtime: {event.reason.value}; "
                    f"work order: {event.work_order_code}"
                ),
            )
        except Exception:
            self.downtime_tracker.remove(
                machine_code=event.machine_code,
                start_time=event.start_time,
                end_time=event.end_time,
            )
            raise

        self._apply_downtime_to_active_task(event)

        return event

    def remove_downtime(
        self,
        machine_code: str,
        start_time: datetime,
        end_time: datetime,
    ) -> DowntimeEvent:
        """
        Xóa downtime.

        Máy chỉ trở về IDLE khi không còn sự kiện downtime nào
        khác của máy trong DowntimeTracker.
        """
        event = self.downtime_tracker.remove(
            machine_code=machine_code,
            start_time=start_time,
            end_time=end_time,
        )

        remaining_events = (
            self.downtime_tracker.find_by_machine(
                event.machine_code
            )
        )

        if not remaining_events:
            self._set_machine_idle_if_possible(
                event.machine_code,
                reason="Downtime removed.",
            )

        return event

    def get_machine_state(
        self,
        machine_code: str,
    ) -> MachineState:
        return self.machine_state_tracker.get_state(
            machine_code
        )

    def get_machine_history(
        self,
        machine_code: str,
    ) -> tuple[MachineStateChange, ...]:
        return self.machine_state_tracker.get_history(
            machine_code
        )

    def get_machine_tasks(
        self,
        machine_code: str,
    ) -> tuple[ExecutionTask, ...]:
        return self.execution_tracker.find_by_machine(
            machine_code
        )

    def _ensure_machine_can_accept_task(
        self,
        task: ExecutionTask,
    ) -> None:
        current_tasks = (
            self.execution_tracker.find_by_machine(
                task.machine_code
            )
        )

        for current_task in current_tasks:
            if current_task.is_terminal:
                continue

            raise MachineBusyError(
                f"Machine {task.machine_code} already has "
                f"an active task: "
                f"{current_task.work_order_code} "
                f"{current_task.op_code}."
            )

    def _ensure_machine_can_start(
        self,
        task: ExecutionTask,
    ) -> None:
        self._ensure_machine_not_in_downtime(
            task.machine_code
        )

        state = self.machine_state_tracker.get_state(
            task.machine_code
        )

        if state is MachineState.OFFLINE:
            raise ExecutionCoordinatorError(
                f"Machine {task.machine_code} is OFFLINE."
            )

        if state is MachineState.MAINTENANCE:
            raise ExecutionCoordinatorError(
                f"Machine {task.machine_code} "
                "is under MAINTENANCE."
            )

    def _ensure_machine_not_in_downtime(
        self,
        machine_code: str,
    ) -> None:
        state = self.machine_state_tracker.get_state(
            machine_code
        )

        if state is MachineState.DOWNTIME:
            raise MachineDowntimeError(
                f"Machine {machine_code} is in DOWNTIME."
            )

    def _set_machine_idle_if_possible(
        self,
        machine_code: str,
        *,
        reason: str,
    ) -> None:
        if machine_code not in self.machine_state_tracker:
            return

        state = self.machine_state_tracker.get_state(
            machine_code
        )

        if state in {
            MachineState.DOWNTIME,
            MachineState.MAINTENANCE,
            MachineState.OFFLINE,
        }:
            return

        self._transition_machine_if_needed(
            machine_code,
            MachineState.IDLE,
            reason=reason,
        )

    def _transition_machine_if_needed(
        self,
        machine_code: str,
        target_state: MachineState,
        *,
        reason: str = "",
    ) -> MachineStateChange | None:
        current_state = (
            self.machine_state_tracker.get_state(
                machine_code
            )
        )

        if current_state is target_state:
            return None

        return self.machine_state_tracker.transition(
            machine_code,
            target_state,
            reason=reason,
        )

    def _apply_downtime_to_active_task(
        self,
        event: DowntimeEvent,
    ) -> None:
        tasks = self.execution_tracker.find_by_machine(
            event.machine_code
        )

        active_statuses = {
            TaskStatus.RUNNING,
            TaskStatus.PAUSED,
        }

        for task in tasks:
            if task.status not in active_statuses:
                continue

            task.downtime_minutes += (
                event.duration_minutes
            )
            break

    def _require_registered_task(
        self,
        task: ExecutionTask,
    ) -> None:
        self._validate_task(task)

        if task not in self.execution_tracker:
            raise ExecutionCoordinatorError(
                "ExecutionTask is not registered "
                "in ExecutionCoordinator."
            )

    @staticmethod
    def _validate_task(
        task: ExecutionTask,
    ) -> None:
        if not isinstance(task, ExecutionTask):
            raise ExecutionCoordinatorError(
                "task must be an ExecutionTask instance."
            )