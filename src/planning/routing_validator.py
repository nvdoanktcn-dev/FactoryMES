from __future__ import annotations

from src.planning.exceptions import InvalidRoutingError
from src.planning.models import Operation, Routing


class RoutingValidator:
    """Kiểm tra dữ liệu routing trước khi tính kế hoạch."""

    @classmethod
    def validate(cls, routing: Routing) -> None:
        if not isinstance(routing, Routing):
            raise InvalidRoutingError(
                "routing must be a Routing instance."
            )

        if not routing.product_code:
            raise InvalidRoutingError(
                "product_code is required."
            )

        if not routing.operations:
            raise InvalidRoutingError(
                "routing must contain at least one operation."
            )

        sequences: set[int] = set()
        op_codes: set[str] = set()

        for operation in routing.operations:
            cls._validate_operation(operation)

            if operation.sequence in sequences:
                raise InvalidRoutingError(
                    "Duplicate operation sequence: "
                    f"{operation.sequence}."
                )

            if operation.op_code in op_codes:
                raise InvalidRoutingError(
                    "Duplicate operation code: "
                    f"{operation.op_code}."
                )

            sequences.add(operation.sequence)
            op_codes.add(operation.op_code)

    @staticmethod
    def _validate_operation(
        operation: Operation,
    ) -> None:
        if not isinstance(operation, Operation):
            raise InvalidRoutingError(
                "All routing items must be Operation instances."
            )

        if not operation.op_code:
            raise InvalidRoutingError(
                "Operation op_code is required."
            )

        if isinstance(operation.sequence, bool):
            raise InvalidRoutingError(
                f"{operation.op_code}: sequence must be an integer."
            )

        if not isinstance(operation.sequence, int):
            raise InvalidRoutingError(
                f"{operation.op_code}: sequence must be an integer."
            )

        if operation.sequence <= 0:
            raise InvalidRoutingError(
                f"{operation.op_code}: sequence must be greater than zero."
            )

        if not operation.machine_group:
            raise InvalidRoutingError(
                f"{operation.op_code}: machine_group is required."
            )

        if operation.cycle_time_sec <= 0:
            raise InvalidRoutingError(
                f"{operation.op_code}: cycle_time_sec "
                "must be greater than zero."
            )

        if operation.setup_time_min < 0:
            raise InvalidRoutingError(
                f"{operation.op_code}: setup_time_min "
                "cannot be negative."
            )

        if isinstance(operation.employee_required, bool):
            raise InvalidRoutingError(
                f"{operation.op_code}: employee_required "
                "must be an integer."
            )

        if operation.employee_required <= 0:
            raise InvalidRoutingError(
                f"{operation.op_code}: employee_required "
                "must be greater than zero."
            )

        if operation.standard_qty <= 0:
            raise InvalidRoutingError(
                f"{operation.op_code}: standard_qty "
                "must be greater than zero."
            )