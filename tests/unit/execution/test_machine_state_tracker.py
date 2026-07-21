import unittest
from datetime import datetime, timedelta

from src.execution import (
    DuplicateMachineError,
    InvalidMachineStateError,
    InvalidMachineTransitionError,
    MachineNotFoundError,
    MachineState,
    MachineStateChange,
    MachineStateTracker,
)


class TestMachineStateTracker(unittest.TestCase):

    def setUp(self) -> None:
        self.tracker = MachineStateTracker()
        self.base_time = datetime(
            2026,
            7,
            20,
            8,
            0,
        )

    def test_register_machine(self) -> None:
        change = self.tracker.register(
            "BL01",
            MachineState.IDLE,
            changed_at=self.base_time,
        )

        self.assertEqual(
            change.machine_code,
            "BL01",
        )
        self.assertEqual(
            self.tracker.get_state("BL01"),
            MachineState.IDLE,
        )

    def test_machine_code_is_normalized(
        self,
    ) -> None:
        self.tracker.register(
            " bl01 ",
            MachineState.IDLE,
        )

        self.assertIn(
            "BL01",
            self.tracker,
        )

    def test_default_state_is_offline(
        self,
    ) -> None:
        self.tracker.register("BL01")

        self.assertEqual(
            self.tracker.get_state("BL01"),
            MachineState.OFFLINE,
        )

    def test_string_state_is_normalized(
        self,
    ) -> None:
        self.tracker.register(
            "BL01",
            "idle",
        )

        self.assertEqual(
            self.tracker.get_state("BL01"),
            MachineState.IDLE,
        )

    def test_duplicate_machine_raises_error(
        self,
    ) -> None:
        self.tracker.register("BL01")

        with self.assertRaises(
            DuplicateMachineError
        ):
            self.tracker.register("bl01")

    def test_empty_machine_code_raises_error(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidMachineStateError
        ):
            self.tracker.register("")

    def test_invalid_state_raises_error(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidMachineStateError
        ):
            self.tracker.register(
                "BL01",
                "UNKNOWN",
            )

    def test_missing_machine_raises_error(
        self,
    ) -> None:
        with self.assertRaises(
            MachineNotFoundError
        ):
            self.tracker.get_state("BL99")

    def test_offline_to_idle(self) -> None:
        self.tracker.register(
            "BL01",
            changed_at=self.base_time,
        )

        change = self.tracker.transition(
            "BL01",
            MachineState.IDLE,
            changed_at=(
                self.base_time
                + timedelta(minutes=1)
            ),
        )

        self.assertEqual(
            change.previous_state,
            MachineState.OFFLINE,
        )
        self.assertEqual(
            change.current_state,
            MachineState.IDLE,
        )

    def test_idle_to_running(self) -> None:
        self.tracker.register(
            "BL01",
            MachineState.IDLE,
        )

        self.tracker.transition(
            "BL01",
            MachineState.RUNNING,
        )

        self.assertEqual(
            self.tracker.get_state("BL01"),
            MachineState.RUNNING,
        )

    def test_running_to_paused(self) -> None:
        self.tracker.register(
            "BL01",
            MachineState.RUNNING,
        )

        self.tracker.transition(
            "BL01",
            MachineState.PAUSED,
        )

        self.assertEqual(
            self.tracker.get_state("BL01"),
            MachineState.PAUSED,
        )

    def test_running_to_downtime(self) -> None:
        self.tracker.register(
            "BL01",
            MachineState.RUNNING,
        )

        self.tracker.transition(
            "BL01",
            MachineState.DOWNTIME,
        )

        self.assertEqual(
            self.tracker.get_state("BL01"),
            MachineState.DOWNTIME,
        )

    def test_invalid_offline_to_running(
        self,
    ) -> None:
        self.tracker.register(
            "BL01",
            MachineState.OFFLINE,
        )

        with self.assertRaises(
            InvalidMachineTransitionError
        ):
            self.tracker.transition(
                "BL01",
                MachineState.RUNNING,
            )

    def test_same_state_transition_raises_error(
        self,
    ) -> None:
        self.tracker.register(
            "BL01",
            MachineState.IDLE,
        )

        with self.assertRaises(
            InvalidMachineTransitionError
        ):
            self.tracker.transition(
                "BL01",
                MachineState.IDLE,
            )

    def test_transition_timestamp_cannot_go_back(
        self,
    ) -> None:
        self.tracker.register(
            "BL01",
            changed_at=self.base_time,
        )

        with self.assertRaises(
            InvalidMachineTransitionError
        ):
            self.tracker.transition(
                "BL01",
                MachineState.IDLE,
                changed_at=(
                    self.base_time
                    - timedelta(minutes=1)
                ),
            )

    def test_history(self) -> None:
        self.tracker.register(
            "BL01",
            changed_at=self.base_time,
        )
        self.tracker.transition(
            "BL01",
            MachineState.IDLE,
            changed_at=(
                self.base_time
                + timedelta(minutes=1)
            ),
        )
        self.tracker.transition(
            "BL01",
            MachineState.RUNNING,
            changed_at=(
                self.base_time
                + timedelta(minutes=2)
            ),
        )

        history = self.tracker.get_history(
            "BL01"
        )

        self.assertEqual(
            len(history),
            3,
        )
        self.assertEqual(
            history[-1].current_state,
            MachineState.RUNNING,
        )

    def test_find_by_state(self) -> None:
        self.tracker.register(
            "BL02",
            MachineState.IDLE,
        )
        self.tracker.register(
            "BL01",
            MachineState.IDLE,
        )
        self.tracker.register(
            "BR01",
            MachineState.RUNNING,
        )

        self.assertEqual(
            self.tracker.find_by_state(
                MachineState.IDLE
            ),
            ("BL01", "BL02"),
        )

    def test_active_machines(self) -> None:
        self.tracker.register(
            "BL01",
            MachineState.RUNNING,
        )
        self.tracker.register(
            "BL02",
            MachineState.IDLE,
        )

        self.assertEqual(
            self.tracker.active_machines,
            ("BL01",),
        )

    def test_available_machines(self) -> None:
        self.tracker.register(
            "BL01",
            MachineState.RUNNING,
        )
        self.tracker.register(
            "BL02",
            MachineState.PAUSED,
        )
        self.tracker.register(
            "BL03",
            MachineState.DOWNTIME,
        )

        self.assertEqual(
            self.tracker.available_machines,
            ("BL01", "BL02"),
        )

    def test_stopped_machines(self) -> None:
        self.tracker.register(
            "BL01",
            MachineState.OFFLINE,
        )
        self.tracker.register(
            "BL02",
            MachineState.DOWNTIME,
        )
        self.tracker.register(
            "BL03",
            MachineState.IDLE,
        )

        self.assertEqual(
            self.tracker.stopped_machines,
            ("BL01", "BL02"),
        )

    def test_count_by_state(self) -> None:
        self.tracker.register(
            "BL01",
            MachineState.IDLE,
        )
        self.tracker.register(
            "BL02",
            MachineState.IDLE,
        )

        self.assertEqual(
            self.tracker.count_by_state(
                MachineState.IDLE
            ),
            2,
        )

    def test_unregister_machine(self) -> None:
        self.tracker.register(
            "BL01",
            MachineState.IDLE,
        )

        removed_state = self.tracker.unregister(
            "BL01"
        )

        self.assertEqual(
            removed_state,
            MachineState.IDLE,
        )
        self.assertNotIn(
            "BL01",
            self.tracker,
        )

    def test_iteration_is_sorted(self) -> None:
        self.tracker.register("BR01")
        self.tracker.register("BL02")
        self.tracker.register("BL01")

        self.assertEqual(
            tuple(self.tracker),
            (
                "BL01",
                "BL02",
                "BR01",
            ),
        )

    def test_clear(self) -> None:
        self.tracker.register("BL01")
        self.tracker.register("BL02")

        self.tracker.clear()

        self.assertEqual(
            len(self.tracker),
            0,
        )

    def test_state_change_validation(self) -> None:
        with self.assertRaises(
            InvalidMachineStateError
        ):
            MachineStateChange(
                machine_code="",
                previous_state=None,
                current_state=MachineState.IDLE,
                changed_at=self.base_time,
            )


if __name__ == "__main__":
    unittest.main()