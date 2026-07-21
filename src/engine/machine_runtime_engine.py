from collections import defaultdict
from datetime import date, datetime

from src.engine.machine_runtime_result import (
    MachineRuntimeResult,
)


class MachineRuntimeEngine:
    """
    Tổng hợp ProductionSnapshot theo máy và ngày.

    Engine thuần:
    - Không truy cập database
    - Không commit
    - Không phụ thuộc SQLAlchemy
    """

    def calculate_daily(
        self,
        snapshots,
        machine_code=None,
        production_date=None,
    ):
        """
        Tổng hợp Runtime theo từng máy và từng ngày.

        Có thể lọc:
        - machine_code
        - production_date
        """
        if snapshots is None:
            snapshots = []

        normalized_machine = self._normalize_code(
            machine_code
        )

        normalized_date = self._normalize_date(
            production_date
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

            if not snapshot_machine:
                continue

            if snapshot_date is None:
                continue

            if (
                normalized_machine
                and snapshot_machine
                != normalized_machine
            ):
                continue

            if (
                normalized_date is not None
                and snapshot_date
                != normalized_date
            ):
                continue

            key = (
                snapshot_machine,
                snapshot_date,
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
        ), values in groups.items():
            results.append(
                MachineRuntimeResult(
                    machine_code=group_machine,
                    production_date=group_date,
                    runtime_sec=values[
                        "runtime_sec"
                    ],
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
            ),
        )

    def calculate_machine_total(
        self,
        snapshots,
        machine_code,
    ):
        """
        Tổng hợp toàn bộ dữ liệu của một máy,
        không phân biệt ngày.
        """
        machine_code = self._normalize_code(
            machine_code
        )

        if not machine_code:
            raise ValueError(
                "Machine Code is required."
            )

        daily_results = self.calculate_daily(
            snapshots=snapshots,
            machine_code=machine_code,
        )

        return {
            "machine_code": machine_code,
            "runtime_sec": sum(
                item.runtime_sec
                for item in daily_results
            ),
            "ok_qty": sum(
                item.ok_qty
                for item in daily_results
            ),
            "ng_qty": sum(
                item.ng_qty
                for item in daily_results
            ),
            "snapshot_count": sum(
                item.snapshot_count
                for item in daily_results
            ),
            "day_count": len(
                daily_results
            ),
        }

    def calculate_date_summary(
        self,
        snapshots,
        production_date,
    ):
        """
        Tổng hợp toàn bộ máy trong một ngày.
        """
        production_date = self._normalize_date(
            production_date
        )

        if production_date is None:
            raise ValueError(
                "Production Date is required."
            )

        daily_results = self.calculate_daily(
            snapshots=snapshots,
            production_date=production_date,
        )

        return {
            "production_date": production_date,
            "machine_count": len(
                daily_results
            ),
            "runtime_sec": sum(
                item.runtime_sec
                for item in daily_results
            ),
            "ok_qty": sum(
                item.ok_qty
                for item in daily_results
            ),
            "ng_qty": sum(
                item.ng_qty
                for item in daily_results
            ),
            "snapshot_count": sum(
                item.snapshot_count
                for item in daily_results
            ),
            "machines": daily_results,
        }

    @staticmethod
    def _normalize_code(value):
        return str(
            value or ""
        ).strip().upper()

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

        return max(
            number,
            0,
        )

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

        return max(
            number,
            0.0,
        )