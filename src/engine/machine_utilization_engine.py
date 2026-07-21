from collections import defaultdict
from datetime import date, datetime

from src.engine.machine_utilization_result import (
    MachineUtilizationResult,
)


class MachineUtilizationEngine:
    """
    Tính tỷ lệ sử dụng máy theo máy, ngày và ca.

    Engine thuần:
    - Không truy cập database
    - Không commit
    - Không phụ thuộc SQLAlchemy
    """

    SHIFT_AVAILABLE_SECONDS = {
        "DAY": 10.5 * 3600,
        "NIGHT": 10.25 * 3600,
    }

    def calculate(
        self,
        snapshots,
        machine_code=None,
        production_date=None,
        shift=None,
    ):
        if snapshots is None:
            snapshots = []

        machine_filter = self._normalize_code(
            machine_code
        )

        date_filter = self._normalize_date(
            production_date
        )

        shift_filter = self._normalize_shift(
            shift
        )

        groups = defaultdict(
            lambda: {
                "runtime_sec": 0.0,
                "ok_qty": 0,
                "ng_qty": 0,
                "snapshot_count": 0,
            }
        )

        for snapshot in snapshots:
            snapshot_machine = self._normalize_code(
                getattr(
                    snapshot,
                    "machine_code",
                    "",
                )
            )

            snapshot_date = self._normalize_date(
                getattr(
                    snapshot,
                    "production_date",
                    None,
                )
            )

            snapshot_shift = self._resolve_snapshot_shift(
                snapshot
            )

            if not snapshot_machine:
                continue

            if snapshot_date is None:
                continue

            if (
                machine_filter
                and snapshot_machine != machine_filter
            ):
                continue

            if (
                date_filter is not None
                and snapshot_date != date_filter
            ):
                continue

            if (
                shift_filter
                and snapshot_shift != shift_filter
            ):
                continue

            key = (
                snapshot_machine,
                snapshot_date,
                snapshot_shift,
            )

            groups[key]["runtime_sec"] += (
                self._to_non_negative_float(
                    getattr(
                        snapshot,
                        "runtime_sec",
                        0,
                    )
                )
            )

            groups[key]["ok_qty"] += (
                self._to_non_negative_int(
                    getattr(
                        snapshot,
                        "ok_qty",
                        0,
                    )
                )
            )

            groups[key]["ng_qty"] += (
                self._to_non_negative_int(
                    getattr(
                        snapshot,
                        "ng_qty",
                        0,
                    )
                )
            )

            groups[key]["snapshot_count"] += 1

        results = []

        for (
            group_machine,
            group_date,
            group_shift,
        ), values in groups.items():
            available_sec = self.get_available_seconds(
                group_shift
            )

            runtime_sec = values["runtime_sec"]

            utilization_percent = self.calculate_percent(
                runtime_sec=runtime_sec,
                available_sec=available_sec,
            )

            results.append(
                MachineUtilizationResult(
                    machine_code=group_machine,
                    production_date=group_date,
                    shift=group_shift,
                    runtime_sec=runtime_sec,
                    available_sec=available_sec,
                    utilization_percent=(
                        utilization_percent
                    ),
                    ok_qty=values["ok_qty"],
                    ng_qty=values["ng_qty"],
                    snapshot_count=values[
                        "snapshot_count"
                    ],
                )
            )

        return sorted(
            results,
            key=lambda item: (
                item.production_date,
                item.machine_code,
                item.shift,
            ),
        )

    def calculate_machine_summary(
        self,
        snapshots,
        machine_code,
    ):
        machine_code = self._normalize_code(
            machine_code
        )

        if not machine_code:
            raise ValueError(
                "Machine Code is required."
            )

        results = self.calculate(
            snapshots=snapshots,
            machine_code=machine_code,
        )

        runtime_sec = sum(
            item.runtime_sec
            for item in results
        )

        available_sec = sum(
            item.available_sec
            for item in results
        )

        return {
            "machine_code": machine_code,
            "runtime_sec": runtime_sec,
            "available_sec": available_sec,
            "utilization_percent":
                self.calculate_percent(
                    runtime_sec,
                    available_sec,
                ),
            "ok_qty": sum(
                item.ok_qty
                for item in results
            ),
            "ng_qty": sum(
                item.ng_qty
                for item in results
            ),
            "shift_count": len(results),
        }

    @classmethod
    def get_available_seconds(cls, shift):
        shift = cls._normalize_shift(shift)

        if shift not in cls.SHIFT_AVAILABLE_SECONDS:
            raise ValueError(
                f"Unsupported shift: {shift}"
            )

        return float(
            cls.SHIFT_AVAILABLE_SECONDS[shift]
        )

    @staticmethod
    def calculate_percent(
        runtime_sec,
        available_sec,
    ):
        runtime_sec = max(
            float(runtime_sec or 0),
            0.0,
        )

        available_sec = max(
            float(available_sec or 0),
            0.0,
        )

        if available_sec <= 0:
            return 0.0

        return min(
            runtime_sec / available_sec * 100,
            100.0,
        )

    @classmethod
    def _resolve_snapshot_shift(
        cls,
        snapshot,
    ):
        explicit_shift = cls._normalize_shift(
            getattr(
                snapshot,
                "shift",
                "",
            )
        )

        if explicit_shift:
            return explicit_shift

        start_time = getattr(
            snapshot,
            "start_time",
            None,
        )

        if isinstance(start_time, datetime):
            hour = start_time.hour

            if 8 <= hour < 20:
                return "DAY"

            return "NIGHT"

        # ProductionSnapshot hiện tại chưa có shift/start_time.
        # Khi không xác định được, dùng DAY để tương thích.
        return "DAY"

    @staticmethod
    def _normalize_code(value):
        return str(
            value or ""
        ).strip().upper()

    @staticmethod
    def _normalize_shift(value):
        text = str(
            value or ""
        ).strip().upper()

        mapping = {
            "DAY": "DAY",
            "D": "DAY",
            "NGÀY": "DAY",
            "CA NGÀY": "DAY",
            "白班": "DAY",

            "NIGHT": "NIGHT",
            "N": "NIGHT",
            "ĐÊM": "NIGHT",
            "CA ĐÊM": "NIGHT",
            "夜班": "NIGHT",
        }

        return mapping.get(text, text)

    @staticmethod
    def _normalize_date(value):
        if value is None or value == "":
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        try:
            return datetime.fromisoformat(
                str(value).strip()
            ).date()

        except ValueError as error:
            raise ValueError(
                f"Invalid date value: {value}"
            ) from error

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

        return max(number, 0)

    @staticmethod
    def _to_non_negative_float(value):
        try:
            number = float(
                value or 0
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0.0

        return max(number, 0.0)