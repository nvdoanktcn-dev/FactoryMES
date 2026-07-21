import unittest
from datetime import datetime, timedelta

from src.execution import (
    DowntimeEvent,
    DowntimeReason,
    InvalidDowntimeEventError,
)


class TestDowntimeEvent(unittest.TestCase):

    def setUp(self) -> None:
        self.start_time = datetime(
            2026,
            7,
            20,
            10,
            0,
        )
        self.end_time = (
            self.start_time
            + timedelta(minutes=30)
        )

    def test_create_downtime_event(self) -> None:
        event = DowntimeEvent(
            machine_code="BL01",
            work_order_code="WO-001",
            reason=DowntimeReason.WAIT_MATERIAL,
            start_time=self.start_time,
            end_time=self.end_time,
        )

        self.assertEqual(
            event.machine_code,
            "BL01",
        )
        self.assertEqual(
            event.duration_minutes,
            30,
        )

    def test_codes_are_normalized(self) -> None:
        event = DowntimeEvent(
            machine_code=" bl01 ",
            work_order_code=" wo-001 ",
            reason=DowntimeReason.REPAIR,
            start_time=self.start_time,
            end_time=self.end_time,
        )

        self.assertEqual(
            event.machine_code,
            "BL01",
        )
        self.assertEqual(
            event.work_order_code,
            "WO-001",
        )

    def test_reason_string_is_normalized(self) -> None:
        event = DowntimeEvent(
            machine_code="BL01",
            work_order_code="WO-001",
            reason="repair",
            start_time=self.start_time,
            end_time=self.end_time,
        )

        self.assertEqual(
            event.reason,
            DowntimeReason.REPAIR,
        )

    def test_empty_machine_code_raises_error(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidDowntimeEventError
        ):
            DowntimeEvent(
                machine_code="",
                work_order_code="WO-001",
                reason=DowntimeReason.REPAIR,
                start_time=self.start_time,
                end_time=self.end_time,
            )

    def test_empty_work_order_raises_error(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidDowntimeEventError
        ):
            DowntimeEvent(
                machine_code="BL01",
                work_order_code="",
                reason=DowntimeReason.REPAIR,
                start_time=self.start_time,
                end_time=self.end_time,
            )

    def test_invalid_reason_raises_error(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidDowntimeEventError
        ):
            DowntimeEvent(
                machine_code="BL01",
                work_order_code="WO-001",
                reason="UNKNOWN",
                start_time=self.start_time,
                end_time=self.end_time,
            )

    def test_end_before_start_raises_error(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidDowntimeEventError
        ):
            DowntimeEvent(
                machine_code="BL01",
                work_order_code="WO-001",
                reason=DowntimeReason.REPAIR,
                start_time=self.start_time,
                end_time=(
                    self.start_time
                    - timedelta(minutes=1)
                ),
            )

    def test_equal_start_end_raises_error(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidDowntimeEventError
        ):
            DowntimeEvent(
                machine_code="BL01",
                work_order_code="WO-001",
                reason=DowntimeReason.REPAIR,
                start_time=self.start_time,
                end_time=self.start_time,
            )

    def test_planned_reason(self) -> None:
        event = DowntimeEvent(
            machine_code="BL01",
            work_order_code="WO-001",
            reason=DowntimeReason.MAINTENANCE,
            start_time=self.start_time,
            end_time=self.end_time,
        )

        self.assertTrue(
            event.is_planned
        )
        self.assertFalse(
            event.is_unplanned
        )

    def test_unplanned_reason(self) -> None:
        event = DowntimeEvent(
            machine_code="BL01",
            work_order_code="WO-001",
            reason=DowntimeReason.REPAIR,
            start_time=self.start_time,
            end_time=self.end_time,
        )

        self.assertTrue(
            event.is_unplanned
        )
        self.assertFalse(
            event.is_planned
        )


if __name__ == "__main__":
    unittest.main()