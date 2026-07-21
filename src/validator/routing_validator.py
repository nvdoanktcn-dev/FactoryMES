from src.database.session import get_session
from src.framework.exception import (
    NotFoundError,
    ValidationError,
)
from src.repository.machine_repository import (
    MachineRepository,
)
from src.repository.product_repository import (
    ProductRepository,
)
from src.repository.routing_repository import (
    RoutingRepository,
)
from src.schema.routing_schema import RoutingSchema


class RoutingValidator:
    """
    Kiểm tra nghiệp vụ Routing với dữ liệu Master.

    Validator truy cập database nhưng không ghi dữ liệu.
    """

    def __init__(self, session=None):
        self.session = session or get_session()

        self.product_repository = ProductRepository(
            self.session
        )

        self.machine_repository = MachineRepository(
            self.session
        )

        self.routing_repository = RoutingRepository(
            self.session
        )

    def validate(
        self,
        data,
        allow_existing=True,
    ):
        RoutingSchema.validate_data(data)

        product_code = data["product_code"]
        machine_code = data["machine_code"]
        op_no = data["op_no"]
        sequence = data["sequence"]

        product = self.product_repository.get_by_code(
            product_code
        )

        if product is None:
            raise NotFoundError(
                f"Product not found: {product_code}"
            )

        machine = self.machine_repository.get_by_code(
            machine_code
        )

        if machine is None:
            raise NotFoundError(
                f"Machine not found: {machine_code}"
            )

        self.validate_machine_type(
            data=data,
            machine=machine,
        )

        self.validate_sequence(
            product_code=product_code,
            op_no=op_no,
            sequence=sequence,
        )

        existing = self.routing_repository.get_by_op(
            product_code,
            op_no,
        )

        if existing is not None and not allow_existing:
            raise ValidationError(
                f"Routing already exists: "
                f"{product_code} - {op_no}"
            )

        return True

    @staticmethod
    def validate_machine_type(data, machine):
        expected_type = (
            RoutingSchema.infer_machine_type(
                data["machine_code"]
            )
        )

        routing_type = str(
            data.get("machine_type", "")
        ).strip().upper()

        master_type = str(
            getattr(machine, "machine_type", "") or ""
        ).strip().upper()

        if (
            expected_type != "OTHER"
            and routing_type != expected_type
        ):
            raise ValidationError(
                f"Machine Type mismatch: "
                f"{data['machine_code']} should be "
                f"{expected_type}, not {routing_type}."
            )

        if (
            master_type
            and master_type != "OTHER"
            and routing_type != master_type
        ):
            raise ValidationError(
                f"Routing Machine Type {routing_type} "
                f"does not match Machine Master "
                f"type {master_type}."
            )

    def validate_sequence(
        self,
        product_code,
        op_no,
        sequence,
    ):
        routings = self.routing_repository.get_by_product(
            product_code
        )

        for routing in routings:
            if routing.op_no == op_no:
                continue

            if int(routing.sequence) == int(sequence):
                raise ValidationError(
                    f"Duplicate Routing Sequence "
                    f"{sequence} for Product "
                    f"{product_code}."
                )

        return True

    def validate_dataframe_records(self, records):
        """
        Kiểm tra trùng OP hoặc Sequence ngay trong file,
        trước khi ghi database.
        """
        errors = []
        seen_ops = set()
        seen_sequences = set()

        for record in records:
            excel_row = record["excel_row"]
            data = record["data"]

            op_key = (
                data["product_code"],
                data["op_no"],
            )

            sequence_key = (
                data["product_code"],
                data["sequence"],
            )

            if op_key in seen_ops:
                errors.append({
                    "row": excel_row,
                    "message": (
                        "Duplicate Product + OP "
                        "inside import file: "
                        f"{data['product_code']} - "
                        f"{data['op_no']}"
                    ),
                })
            else:
                seen_ops.add(op_key)

            if sequence_key in seen_sequences:
                errors.append({
                    "row": excel_row,
                    "message": (
                        "Duplicate Product + Sequence "
                        "inside import file: "
                        f"{data['product_code']} - "
                        f"{data['sequence']}"
                    ),
                })
            else:
                seen_sequences.add(sequence_key)

        return errors