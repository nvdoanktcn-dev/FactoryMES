from datetime import datetime

from src.engine.production_snapshot import (
    ProductionSnapshot,
)


class ProductionSnapshotEngine:
    """
    Chuyển Production Log thành Snapshot.
    """

    @staticmethod
    def runtime_seconds(
        start_time,
        end_time,
    ):
        """
        Tính Runtime theo giây.
        """

        if (
            start_time is None
            or end_time is None
        ):
            return 0

        if isinstance(
            start_time,
            str,
        ):
            start_time = datetime.fromisoformat(
                start_time
            )

        if isinstance(
            end_time,
            str,
        ):
            end_time = datetime.fromisoformat(
                end_time
            )

        seconds = int(
            (
                end_time
                - start_time
            ).total_seconds()
        )

        return max(
            seconds,
            0,
        )

    @classmethod
    def create_snapshot(
        cls,
        production_log,
    ):
        runtime = cls.runtime_seconds(
            production_log.start_time,
            production_log.end_time,
        )

        return ProductionSnapshot(
            work_order_no=production_log.work_order_no,

            product_code=production_log.product_code,

            op_no=production_log.op_no,

            machine_code=production_log.machine_code,

            operator_code=production_log.operator_code,

            production_date=production_log.production_date,

            runtime_sec=runtime,

            ok_qty=production_log.ok_qty,

            ng_qty=production_log.ng_qty,
        )

    @classmethod
    def create_snapshots(
        cls,
        production_logs,
    ):
        return [
            cls.create_snapshot(log)
            for log in production_logs
        ]