import unittest
from datetime import datetime, timedelta

from src.execution import (
    DowntimeEvent,
    DowntimeEventNotFoundError,
    DowntimeReason,
    DowntimeTracker,
    DuplicateDowntimeEventError,
    InvalidDowntimeEventError,
)


class TestDowntimeTracker(unittest.TestCase):

    def setUp(self) -> None:
        self.tracker = DowntimeTracker()

        self.base_time = datetime(
            2026,
            7,
            20,
            8,
            0,
        )

        self.event_1 = self._create_event(
            machine_code="BL01",
            work_order_code="WO-001",
            reason=DowntimeReason.WAIT_MATERIAL,
            start_offset=0,
            duration=30,
        )

        self.event_2 = self._create_event(
            machine_code="BL01",
            work_order_code="WO-001",
            reason=DowntimeReason.MAINTENANCE,
            start_offset=60,
            duration=20,
        )

        self.event_3 = self._create_event(
            machine_code="BR01",
            work_order_code="WO-002",
            reason=DowntimeReason.REPAIR,
            start_offset=10,
            duration=40,
        )

    def _create_event(
        self,
        machine_code: str,
        work_order_code: str,
        reason: DowntimeReason,
        start_offset: int,
        duration: int,
    ) -> DowntimeEvent:
        start_time = (
            self.base_time
            + timedelta(minutes=start_offset)
        )

        return DowntimeEvent(
            machine_code=machine_code,
            work_order_code=work_order_code,
            reason=reason,
            start_time=start_time,
            end_time=(
                start_time
                + timedelta(minutes=duration)
            ),
        )

    def test_add_event(self) -> None:
        self.tracker.add(self.event_1)

        self.assertEqual(
            self.tracker.total_events,
            1,
        )

    def test_get_event(self) -> None:
        self.tracker.add(self.event_1)

        result = self.tracker.get(
            machine_code="BL01",
            start_time=self.event_1.start_time,
            end_time=self.event_1.end_time,
        )

        self.assertIs(
            result,
            self.event_1,
        )

    def test_duplicate_event_raises_error(
        self,
    ) -> None:
        self.tracker.add(self.event_1)

        with self.assertRaises(
            DuplicateDowntimeEventError
        ):
            self.tracker.add(self.event_1)

    def test_missing_event_raises_error(
        self,
    ) -> None:
        with self.assertRaises(
            DowntimeEventNotFoundError
        ):
            self.tracker.get(
                machine_code="BL99",
                start_time=self.event_1.start_time,
                end_time=self.event_1.end_time,
            )

    def test_remove_event(self) -> None:
        self.tracker.add(self.event_1)

        removed = self.tracker.remove(
            machine_code="BL01",
            start_time=self.event_1.start_time,
            end_time=self.event_1.end_time,
        )

        self.assertIs(
            removed,
            self.event_1,
        )
        self.assertEqual(
            len(self.tracker),
            0,
        )

    def test_find_by_machine(self) -> None:
        self.tracker.add(self.event_1)
        self.tracker.add(self.event_2)
        self.tracker.add(self.event_3)

        result = self.tracker.find_by_machine(
            "BL01"
        )

        self.assertEqual(
            len(result),
            2,
        )

    def test_find_by_work_order(self) -> None:
        self.tracker.add(self.event_1)
        self.tracker.add(self.event_2)
        self.tracker.add(self.event_3)

        result = self.tracker.find_by_work_order(
            "WO-001"
        )

        self.assertEqual(
            len(result),
            2,
        )

    def test_find_by_reason(self) -> None:
        self.tracker.add(self.event_1)
        self.tracker.add(self.event_2)
        self.tracker.add(self.event_3)

        result = self.tracker.find_by_reason(
            DowntimeReason.REPAIR
        )

        self.assertEqual(
            result,
            (self.event_3,),
        )

    def test_total_minutes(self) -> None:
        self.tracker.add(self.event_1)
        self.tracker.add(self.event_2)
        self.tracker.add(self.event_3)

        self.assertEqual(
            self.tracker.total_minutes,
            90,
        )

    def test_planned_minutes(self) -> None:
        self.tracker.add(self.event_1)
        self.tracker.add(self.event_2)
        self.tracker.add(self.event_3)

        self.assertEqual(
            self.tracker.planned_minutes,
            20,
        )

    def test_unplanned_minutes(self) -> None:
        self.tracker.add(self.event_1)
        self.tracker.add(self.event_2)
        self.tracker.add(self.event_3)

        self.assertEqual(
            self.tracker.unplanned_minutes,
            70,
        )

    def test_total_minutes_by_machine(
        self,
    ) -> None:
        self.tracker.add(self.event_1)
        self.tracker.add(self.event_2)
        self.tracker.add(self.event_3)

        self.assertEqual(
            self.tracker.total_minutes_by_machine(
                "BL01"
            ),
            50,
        )

    def test_total_minutes_by_reason(
        self,
    ) -> None:
        self.tracker.add(self.event_1)
        self.tracker.add(self.event_2)

        self.assertEqual(
            self.tracker.total_minutes_by_reason(
                DowntimeReason.MAINTENANCE
            ),
            20,
        )

    def test_planned_events(self) -> None:
        self.tracker.add(self.event_1)
        self.tracker.add(self.event_2)

        self.assertEqual(
            self.tracker.find_planned(),
            (self.event_2,),
        )

    def test_unplanned_events(self) -> None:
        self.tracker.add(self.event_1)
        self.tracker.add(self.event_2)

        self.assertEqual(
            self.tracker.find_unplanned(),
            (self.event_1,),
        )

    def test_same_machine_overlap_raises_error(
        self,
    ) -> None:
        self.tracker.add(self.event_1)

        overlapping = self._create_event(
            machine_code="BL01",
            work_order_code="WO-001",
            reason=DowntimeReason.REPAIR,
            start_offset=20,
            duration=30,
        )

        with self.assertRaises(
            InvalidDowntimeEventError
        ):
            self.tracker.add(overlapping)

    def test_different_machine_can_overlap(
        self,
    ) -> None:
        self.tracker.add(self.event_1)
        self.tracker.add(self.event_3)

        self.assertEqual(
            len(self.tracker),
            2,
        )

    def test_adjacent_events_do_not_overlap(
        self,
    ) -> None:
        self.tracker.add(self.event_1)

        adjacent = self._create_event(
            machine_code="BL01",
            work_order_code="WO-001",
            reason=DowntimeReason.REPAIR,
            start_offset=30,
            duration=10,
        )

        self.tracker.add(adjacent)

        self.assertEqual(
            len(self.tracker),
            2,
        )

    def test_contains_event(self) -> None:
        self.tracker.add(self.event_1)

        self.assertIn(
            self.event_1,
            self.tracker,
        )

    def test_iteration_is_sorted(self) -> None:
        self.tracker.add(self.event_2)
        self.tracker.add(self.event_1)

        self.assertEqual(
            tuple(self.tracker),
            (
                self.event_1,
                self.event_2,
            ),
        )

    def test_clear(self) -> None:
        self.tracker.add(self.event_1)
        self.tracker.add(self.event_2)

        self.tracker.clear()

        self.assertEqual(
            len(self.tracker),
            0,
        )

    def test_invalid_event_raises_error(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidDowntimeEventError
        ):
            self.tracker.add(None)


if __name__ == "__main__":
    unittest.main()