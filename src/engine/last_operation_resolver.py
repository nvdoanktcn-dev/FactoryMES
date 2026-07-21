from collections import Counter

from src.engine.last_operation_result import (
    LastOperationResult,
)


class LastOperationResolver:
    """
    Tính sản lượng hoàn thành theo OP cuối của Routing.

    Engine này không truy cập database.

    Input:
        work_order_no
        last_operation
        production snapshots

    Output:
        LastOperationResult
    """

    def resolve(
        self,
        work_order_no,
        last_operation,
        snapshots,
    ):
        work_order_no = self._normalize_text(
            work_order_no
        ).upper()

        if not work_order_no:
            raise ValueError(
                "Work Order No is required."
            )

        last_op = self._resolve_last_op(
            last_operation
        )

        if not last_op:
            raise ValueError(
                "Last Operation is required."
            )

        if snapshots is None:
            snapshots = []

        matched_snapshots = [
            snapshot
            for snapshot in snapshots
            if (
                self._normalize_text(
                    getattr(
                        snapshot,
                        "work_order_no",
                        "",
                    )
                ).upper()
                == work_order_no
                and self._normalize_op(
                    getattr(
                        snapshot,
                        "op_no",
                        "",
                    )
                )
                == last_op
            )
        ]

        product_code = self._resolve_product_code(
            matched_snapshots,
            snapshots,
            work_order_no,
        )

        machine_code = self._resolve_machine_code(
            matched_snapshots
        )

        ok_qty = sum(
            self._to_non_negative_int(
                getattr(
                    snapshot,
                    "ok_qty",
                    0,
                )
            )
            for snapshot in matched_snapshots
        )

        ng_qty = sum(
            self._to_non_negative_int(
                getattr(
                    snapshot,
                    "ng_qty",
                    0,
                )
            )
            for snapshot in matched_snapshots
        )

        runtime_sec = sum(
            self._to_non_negative_float(
                getattr(
                    snapshot,
                    "runtime_sec",
                    0,
                )
            )
            for snapshot in matched_snapshots
        )

        return LastOperationResult(
            work_order_no=work_order_no,
            product_code=product_code,
            last_op=last_op,
            machine_code=machine_code,
            runtime_sec=runtime_sec,
            ok_qty=ok_qty,
            ng_qty=ng_qty,
            snapshot_count=len(
                matched_snapshots
            ),
        )

    @classmethod
    def _resolve_last_op(cls, last_operation):
        """
        Hỗ trợ:
        - string: "OP30"
        - object có thuộc tính op_no
        - dictionary có key op_no
        """
        if last_operation is None:
            return ""

        if isinstance(
            last_operation,
            str,
        ):
            return cls._normalize_op(
                last_operation
            )

        if isinstance(
            last_operation,
            dict,
        ):
            return cls._normalize_op(
                last_operation.get(
                    "op_no",
                    "",
                )
            )

        return cls._normalize_op(
            getattr(
                last_operation,
                "op_no",
                "",
            )
        )

    @classmethod
    def _resolve_product_code(
        cls,
        matched_snapshots,
        all_snapshots,
        work_order_no,
    ):
        for snapshot in matched_snapshots:
            product_code = cls._normalize_text(
                getattr(
                    snapshot,
                    "product_code",
                    "",
                )
            ).upper()

            if product_code:
                return product_code

        for snapshot in all_snapshots:
            snapshot_work_order = (
                cls._normalize_text(
                    getattr(
                        snapshot,
                        "work_order_no",
                        "",
                    )
                ).upper()
            )

            if snapshot_work_order != work_order_no:
                continue

            product_code = cls._normalize_text(
                getattr(
                    snapshot,
                    "product_code",
                    "",
                )
            ).upper()

            if product_code:
                return product_code

        return ""

    @classmethod
    def _resolve_machine_code(
        cls,
        snapshots,
    ):
        """
        Nếu OP cuối chạy trên nhiều máy,
        trả về máy xuất hiện nhiều nhất.

        Khi số lần bằng nhau, ưu tiên máy
        xuất hiện đầu tiên trong dữ liệu.
        """
        machine_codes = [
            cls._normalize_text(
                getattr(
                    snapshot,
                    "machine_code",
                    "",
                )
            ).upper()
            for snapshot in snapshots
        ]

        machine_codes = [
            code
            for code in machine_codes
            if code
        ]

        if not machine_codes:
            return ""

        counts = Counter(machine_codes)
        highest_count = max(
            counts.values()
        )

        for machine_code in machine_codes:
            if (
                counts[machine_code]
                == highest_count
            ):
                return machine_code

        return ""

    @staticmethod
    def _normalize_op(value):
        text = LastOperationResolver._normalize_text(
            value
        ).upper()

        if not text:
            return ""

        digits = "".join(
            character
            for character in text
            if character.isdigit()
        )

        if digits:
            return f"OP{int(digits)}"

        return text

    @staticmethod
    def _normalize_text(value):
        if value is None:
            return ""

        text = str(value).strip()

        if text.lower() in {
            "nan",
            "none",
            "nat",
        }:
            return ""

        return " ".join(
            text.split()
        )

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