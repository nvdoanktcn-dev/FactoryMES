from __future__ import annotations

import re
from collections import defaultdict
from math import ceil

from src.framework.exception import (
    DuplicateError,
    NotFoundError,
)
from src.framework.validator import BaseValidator
from src.models.routing import Routing
from src.repository.routing_repository import (
    RoutingRepository,
)
from src.repository.product_repository import (
    ProductRepository,
)
from src.services.base_service import SessionOwnedService
from sqlalchemy.orm import Session


class RoutingService(SessionOwnedService):
    STATUS_ACTIVE = "ACTIVE"
    STATUS_INACTIVE = "INACTIVE"

    VALID_STATUS = {
        STATUS_ACTIVE,
        STATUS_INACTIVE,
    }

    VALID_PROCESS_TYPES = {
        "CNC",
        "ROBOT",
        "MANUAL",
        "INSPECTION",
        "OTHER",
    }

    def __init__(
        self,
        session: Session | None = None,
        repository: RoutingRepository | None = None,
    ):
        if repository is not None:
            repository_session = getattr(
                repository,
                "session",
                None,
            )
            super().__init__(
                session=repository_session,
            )
            self._owns_session = False
            self.repository = repository
            self.product_repository = (
                ProductRepository(
                    self.require_session()
                )
            )
            return

        super().__init__(
            session=session,
        )
        self.repository = RoutingRepository(
            self.require_session()
        )
        self.product_repository = ProductRepository(
            self.require_session()
        )

    # ==========================================================
    # Query
    # ==========================================================

    def get_all_routings(self):
        return self.repository.get_all()

    def get_routing(
        self,
        product_code,
        operation_no,
    ):
        code = self._normalize_code(
            product_code
        )

        operation = self._normalize_operation_no(
            operation_no
        )

        if not code:
            return None

        return self.repository.get_by_product_operation(
            code,
            operation,
        )

    def get_by_product_operation(
        self,
        product_code,
        operation_no,
    ):
        return self.get_routing(
            product_code,
            operation_no,
        )

    def get_product_routing(
        self,
        product_code,
    ):
        return self.repository.get_by_product(
            product_code
        )

    def get_last_operation(
        self,
        product_code,
    ):
        return self.repository.get_last_operation(
            product_code
        )

    def build_capacity_profile(
        self,
        routings,
    ):
        """
        Return calculated capacity information without changing schema.

        The first ACTIVE operation of each product is the reference.
        Later operations require ceil(cycle/reference_cycle) machines.
        The highest ACTIVE operation number is the final operation.
        """
        grouped = defaultdict(list)

        for routing in routings or []:
            if str(
                routing.status or ""
            ).strip().upper() != self.STATUS_ACTIVE:
                continue

            grouped[
                self._normalize_code(
                    routing.product_code
                )
            ].append(routing)

        profile = {}

        for product_code, operations in grouped.items():
            operations.sort(
                key=lambda item: int(
                    item.operation_no or 0
                )
            )

            if not operations:
                continue

            reference_cycle = float(
                operations[
                    0
                ].standard_cycle_time_sec
                or 0
            )

            if reference_cycle <= 0:
                continue

            final_operation_no = int(
                operations[-1].operation_no
            )

            for routing in operations:
                cycle_time = float(
                    routing.standard_cycle_time_sec
                    or 0
                )
                required_machines = max(
                    1,
                    ceil(
                        cycle_time
                        / reference_cycle
                    ),
                )
                key = (
                    product_code,
                    int(routing.operation_no),
                )
                profile[key] = {
                    "reference_cycle_time_sec":
                        reference_cycle,
                    "required_machine_count":
                        required_machines,
                    "is_final_operation": (
                        int(routing.operation_no)
                        == final_operation_no
                    ),
                }

        return profile

    def get_by_import_key(
        self,
        entity_key,
    ):
        text = str(    
            entity_key or ""
        ).strip()

        if "|" not in text:
            raise ValueError(
                (
                    "Invalid Routing import key: "
                    f"{entity_key}"
                )
            )

        product_code, operation_no = (
            text.split(
                "|",
                1,
            )
        )

        return self.get_routing(
                product_code,
            operation_no,
        )

    # ==========================================================
    # Create
    # ==========================================================

    def create_routing(
        self,
        data,
    ):
        normalized = self._normalize_data(
            data
        )

        self._validate_routing(
            normalized
        )
        self._validate_product_exists(
            normalized["product_code"]
        )

        product_code = normalized[
            "product_code"
        ]

        operation_no = normalized[
            "operation_no"
        ]

        if self.repository.exists(
            product_code,
            operation_no,
        ):
            raise DuplicateError(
                (
                    "Routing already exists: "
                    f"{product_code} / OP{operation_no}"
                )
            )

        routing = Routing(
            product_code=normalized["product_code"],
            operation_no=normalized["operation_no"],
            operation_name=normalized["operation_name"],
            process_type=normalized["process_type"],
            machine_type=normalized["machine_type"],
            standard_cycle_time_sec=normalized[
                "standard_cycle_time_sec"
            ],
            standard_output_pcs_hour=normalized[
                "standard_output_pcs_hour"
            ],
            standard_operator_count=normalized[
                "standard_operator_count"
            ],
            status=normalized["status"],
            remark=normalized["remark"],
        )
        
        self.log_info(
            (
                "Create Routing: "
                f"{product_code} / OP{operation_no}"
            )
        )

        return self.repository.add(
            routing
        )

    # ==========================================================
    # Update
    # ==========================================================

    def update_routing(
        self,
        product_code,
        operation_no,
        data,
    ):
        code = self._normalize_code(
            product_code
        )

        operation = self._normalize_operation_no(
            operation_no
        )

        routing = (
            self.repository
            .get_by_product_operation(
                code,
                operation,
            )
        )

        if routing is None:
            raise NotFoundError(
                (
                    "Routing not found: "
                    f"{code} / OP{operation}"
                )
            )

        normalized = self._normalize_data(
            {
                **dict(data or {}),
                "product_code": code,
                "operation_no": operation,
            }
        )

        self._validate_routing(
            normalized
        )
        self._validate_product_exists(
            normalized["product_code"]
        )

        routing.operation_name = normalized[
            "operation_name"
        ]

        routing.process_type = normalized[
            "process_type"
        ]

        routing.machine_type = normalized[
            "machine_type"
        ]

        routing.standard_cycle_time_sec = (
            normalized[
                "standard_cycle_time_sec"
            ]
        )

        routing.standard_output_pcs_hour = (
            normalized[
                "standard_output_pcs_hour"
            ]
        )

        routing.standard_operator_count = (
            normalized[
                "standard_operator_count"
            ]
        )

        routing.status = normalized[
            "status"
        ]

        routing.remark = normalized[
            "remark"
        ]

        self.repository.update()

        return routing

    # ==========================================================
    # Upsert for Import
    # ==========================================================

    def save_routing(
        self,
        data,
    ):
        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                "Routing data must be a dictionary."
            )

        product_code = self._normalize_code(
            data.get(
                "product_code"
            )
        )

        operation_no = self._normalize_operation_no(
            data.get(
                "operation_no"
            )
        )

        existing = (
            self.repository
            .get_by_product_operation(
                product_code,
                operation_no,
            )
        )

        if existing is None:
            routing = self.create_routing(
                data
            )

            return routing, "created"

        routing = self.update_routing(
            product_code,
            operation_no,
            data,
        )

        return routing, "updated"

    # ==========================================================
    # Inactive
    # ==========================================================

    def delete_routing(
        self,
        product_code,
        operation_no,
    ):
        routing = self.get_routing(
            product_code,
            operation_no,
        )

        if routing is None:
            raise NotFoundError(
                (
                    "Routing not found: "
                    f"{product_code} / {operation_no}"
                )
            )

        return self.set_routing_status(
            product_code,
            operation_no,
            self.STATUS_INACTIVE,
        )

    def activate_routing(
        self,
        product_code,
        operation_no,
    ):
        return self.set_routing_status(
            product_code,
            operation_no,
            self.STATUS_ACTIVE,
        )

    def set_routing_status(
        self,
        product_code,
        operation_no,
        status,
    ):
        routing = self.get_routing(
            product_code,
            operation_no,
        )

        if routing is None:
            raise NotFoundError(
                (
                    "Routing not found: "
                    f"{product_code} / {operation_no}"
                )
            )

        routing.status = self._normalize_status(
            status
        )
        self.repository.update()

        return routing

    # ==========================================================
    # Transaction
    # ==========================================================

    def commit(self):
        self.require_session().commit()

    def rollback(self):
        session = self.require_session()

        if session.is_active:
            session.rollback()

    # ==========================================================
    # Validation
    # ==========================================================

    @classmethod
    def _validate_routing(
        cls,
        data,
    ):
        BaseValidator.required(
            data["product_code"],
            "Product Code",
        )

        BaseValidator.required(
            data["operation_name"],
            "Operation Name",
        )

        BaseValidator.required(
            data["process_type"],
            "Process Type",
        )

        if data["operation_no"] <= 0:
            raise ValueError(
                "Operation No must be greater than zero."
            )

        if (
            data["standard_cycle_time_sec"]
            <= 0
        ):
            raise ValueError(
                (
                    "Standard Cycle Time must be "
                    "greater than zero."
                )
            )

        if (
            data["standard_output_pcs_hour"]
            < 0
        ):
            raise ValueError(
                (
                    "Standard Output cannot "
                    "be negative."
                )
            )

        if (
            data["standard_operator_count"]
            <= 0
        ):
            raise ValueError(
                (
                    "Standard Operator Count must "
                    "be greater than zero."
                )
            )

        process_type = data["process_type"]
        machine_type = data["machine_type"]

        if (
            process_type in {"CNC", "ROBOT"}
            and machine_type != process_type
        ):
            raise ValueError(
                (
                    f"{process_type} process requires "
                    f"Machine Type {process_type}."
                )
            )

    def _validate_product_exists(
        self,
        product_code,
    ):
        if (
            self.product_repository.get_by_code(
                product_code
            )
            is None
        ):
            raise ValueError(
                (
                    "Product does not exist: "
                    f"{product_code}"
                )
            )

    # ==========================================================
    # Normalization
    # ==========================================================

    @classmethod
    def _normalize_data(
        cls,
        data,
    ):
        data = dict(
            data or {}
        )

        cycle_time = cls._to_float(
            data.get(
                "standard_cycle_time_sec"
            ),
            default=0.0,
        )

        standard_output = 0.0

        if cycle_time > 0:
            standard_output = (
                3600.0 / cycle_time
            )

        process_type = cls._normalize_process_type(
            data.get(
                "process_type"
            )
        )
        machine_type = cls._normalize_machine_type(
            data.get(
                "machine_type"
            ),
            process_type=process_type,
        )

        return {
            "product_code": cls._normalize_code(
                data.get(
                    "product_code"
                )
            ),
            "operation_no": (
                cls._normalize_operation_no(
                    data.get(
                        "operation_no"
                    )
                )
            ),
            "operation_name": cls._clean_text(
                data.get(
                    "operation_name"
                )
            ),
            "process_type": process_type,
            "machine_type": machine_type,
            "standard_cycle_time_sec": (
                cycle_time
            ),
            "standard_output_pcs_hour": (
                standard_output
            ),
            "standard_operator_count": (
                cls._to_float(
                    data.get(
                        "standard_operator_count"
                    ),
                    default=1.0,
                )
            ),
            "status": cls._normalize_status(
                data.get(
                    "status"
                )
            ),
            "remark": cls._clean_optional_text(
                data.get(
                    "remark"
                )
            ),
        }

    @staticmethod
    def _normalize_code(
        value,
    ):
        return str(
            value or ""
        ).strip().upper()

    @staticmethod
    def _normalize_operation_no(
        value,
    ):
        if isinstance(
            value,
            str,
        ):
            text = value.strip().upper()

            match = re.fullmatch(
                r"OP\s*(\d+)",
                text,
            )

            if match:
                return int(
                    match.group(1)
                )

        try:
            operation_no = int(
                float(value)
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                (
                    "Invalid Operation No: "
                    f"{value}"
                )
            ) from error

        if operation_no <= 0:
            raise ValueError(
                (
                    "Operation No must be "
                    "greater than zero."
                )
            )

        return operation_no

    @classmethod
    def _normalize_process_type(
        cls,
        value,
    ):
        process_type = str(
            value or ""
        ).strip().upper()

        if not process_type:
            raise ValueError(
                "Process Type is required."
            )

        if (
            process_type
            not in cls.VALID_PROCESS_TYPES
        ):
            raise ValueError(
                (
                    "Invalid Process Type: "
                    f"{process_type}"
                )
            )

        return process_type

    @classmethod
    def _normalize_status(
        cls,
        value,
    ):
        status = str(
            value
            or cls.STATUS_ACTIVE
        ).strip().upper()

        if status not in cls.VALID_STATUS:
            raise ValueError(
                (
                    "Invalid Routing Status: "
                    f"{status}"
                )
            )

        return status

    @staticmethod
    def _normalize_machine_type(
        value,
        *,
        process_type,
    ):
        machine_type = str(
            value or ""
        ).strip().upper()

        if (
            not machine_type
            and process_type in {"CNC", "ROBOT"}
        ):
            return process_type

        return machine_type or None

    @staticmethod
    def _clean_text(
        value,
    ):
        return str(
            value or ""
        ).strip()

    @staticmethod
    def _clean_optional_text(
        value,
    ):
        text = str(
            value or ""
        ).strip()

        return text or None

    @staticmethod
    def _to_float(
        value,
        default=0.0,
    ):
        if value in {
            None,
            "",
        }:
            return float(
                default
            )

        try:
            return float(
                value
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"Invalid numeric value: {value}"
            ) from error
