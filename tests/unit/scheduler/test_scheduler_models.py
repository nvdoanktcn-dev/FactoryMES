import unittest
from datetime import datetime, timedelta

from src.scheduler.exceptions import (
    InvalidBookingError,
    InvalidScheduleInputError,
)
from src.scheduler.models import (
    MachineBooking,
    ScheduleResult,
)


class TestMachineBooking(unittest.TestCase):

    def setUp(self) -> None:
        self.start_time = datetime(
            2026,
            7,
            20,
            8,
            0,
        )
        self.end_time = self.start_time + timedelta(
            minutes=60
        )

    def create_booking(
        self,
        **overrides,
    ) -> MachineBooking:
        values = {
            "work_order_code": "WO-001",
            "product_code": "P-001",
            "machine_group": "cnc",
            "machine_code": "bl01",
            "op_code": "op10",
            "sequence": 10,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "quantity": 100,
        }
        values.update(overrides)

        return MachineBooking(**values)

    def test_create_machine_booking(self) -> None:
        booking = self.create_booking()

        self.assertEqual(
            booking.work_order_code,
            "WO-001",
        )
        self.assertEqual(
            booking.product_code,
            "P-001",
        )
        self.assertEqual(
            booking.machine_group,
            "CNC",
        )
        self.assertEqual(
            booking.machine_code,
            "BL01",
        )
        self.assertEqual(
            booking.op_code,
            "OP10",
        )

    def test_duration_minutes(self) -> None:
        booking = self.create_booking()

        self.assertEqual(
            booking.duration_minutes,
            60.0,
        )

    def test_end_time_equal_start_time_raises_error(
        self,
    ) -> None:
        with self.assertRaises(InvalidBookingError):
            self.create_booking(
                end_time=self.start_time,
            )

    def test_end_time_before_start_time_raises_error(
        self,
    ) -> None:
        with self.assertRaises(InvalidBookingError):
            self.create_booking(
                end_time=(
                    self.start_time
                    - timedelta(minutes=1)
                ),
            )

    def test_zero_quantity_raises_error(self) -> None:
        with self.assertRaises(InvalidBookingError):
            self.create_booking(quantity=0)

    def test_empty_machine_code_raises_error(
        self,
    ) -> None:
        with self.assertRaises(InvalidBookingError):
            self.create_booking(machine_code=" ")

    def test_invalid_sequence_raises_error(self) -> None:
        with self.assertRaises(InvalidBookingError):
            self.create_booking(sequence=0)


class TestScheduleResult(unittest.TestCase):

    def setUp(self) -> None:
        self.start_time = datetime(
            2026,
            7,
            20,
            8,
            0,
        )

        self.booking = MachineBooking(
            work_order_code="WO-001",
            product_code="P-001",
            machine_group="CNC",
            machine_code="BL01",
            op_code="OP10",
            sequence=10,
            start_time=self.start_time,
            end_time=(
                self.start_time
                + timedelta(minutes=60)
            ),
            quantity=100,
        )

    def test_create_schedule_result(self) -> None:
        result = ScheduleResult(
            work_order_code="WO-001",
            product_code="P-001",
            bookings=(self.booking,),
            start_time=self.start_time,
            finish_time=self.booking.end_time,
        )

        self.assertEqual(result.total_bookings, 1)
        self.assertEqual(
            result.total_duration_minutes,
            60.0,
        )

    def test_booking_list_is_converted_to_tuple(
        self,
    ) -> None:
        result = ScheduleResult(
            work_order_code="WO-001",
            product_code="P-001",
            bookings=[self.booking],
            start_time=self.start_time,
            finish_time=self.booking.end_time,
        )

        self.assertIsInstance(
            result.bookings,
            tuple,
        )

    def test_finish_before_start_raises_error(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidScheduleInputError
        ):
            ScheduleResult(
                work_order_code="WO-001",
                product_code="P-001",
                bookings=(),
                start_time=self.start_time,
                finish_time=(
                    self.start_time
                    - timedelta(minutes=1)
                ),
            )

    def test_different_work_order_raises_error(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidScheduleInputError
        ):
            ScheduleResult(
                work_order_code="WO-002",
                product_code="P-001",
                bookings=(self.booking,),
                start_time=self.start_time,
                finish_time=self.booking.end_time,
            )

    def test_different_product_raises_error(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidScheduleInputError
        ):
            ScheduleResult(
                work_order_code="WO-001",
                product_code="P-002",
                bookings=(self.booking,),
                start_time=self.start_time,
                finish_time=self.booking.end_time,
            )


if __name__ == "__main__":
    unittest.main()