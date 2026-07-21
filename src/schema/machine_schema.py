from __future__ import annotations

from src.services.master_import.schema.base_schema import (
    BaseSchema,
)


class MachineSchema(BaseSchema):
    REQUIRED_COLUMNS = [
        "Machine Code",
        "Machine Name",
        "Machine Type",
    ]

    OPTIONAL_COLUMNS = [
        "Line",
        "Location",
        "Brand",
        "Model",
        "Serial Number",
        "Status",
    ]

    VALID_STATUS = {
        "ACTIVE",
        "RUNNING",
        "STOPPED",
        "MAINTENANCE",
        "INACTIVE",
    }

    VALID_MACHINE_TYPES = {
        "CNC",
        "ROBOT",
    }

    @staticmethod
    def normalize_machine_type(machine_type):
        if machine_type is None:
            return ""

        value = str(machine_type).strip().upper()

        mapping = {
            "BL": "CNC",
            "CNC": "CNC",
            "LATHE": "CNC",
            "MILLING": "CNC",

            "BR": "ROBOT",
            "ASK": "ROBOT",
            "ROBOT": "ROBOT",
            "ROBOTIC": "ROBOT",
        }

        return mapping.get(value, value)

    @staticmethod
    def normalize_status(status):
        if status is None:
            return "ACTIVE"

        value = str(status).strip().upper()

        if not value:
            return "ACTIVE"

        mapping = {
            "ACTIVE": "ACTIVE",
            "HOẠT ĐỘNG": "ACTIVE",
            "HOAT DONG": "ACTIVE",
            "ENABLED": "ACTIVE",
    
            "RUN": "RUNNING",
            "RUNNING": "RUNNING",

            "STOP": "STOPPED",
            "STOPPED": "STOPPED",
            "DỪNG": "STOPPED",
            "DUNG": "STOPPED",

            "MAINTENANCE": "MAINTENANCE",
            "MAINTAIN": "MAINTENANCE",
            "PM": "MAINTENANCE",
            "BẢO TRÌ": "MAINTENANCE",
            "BAO TRI": "MAINTENANCE",

            "INACTIVE": "INACTIVE",
            "IDLE": "INACTIVE",
            "KHÔNG HOẠT ĐỘNG": "INACTIVE",
            "KHONG HOAT DONG": "INACTIVE",
            "DISABLED": "INACTIVE",
        }

        return mapping.get(value, value)

    @staticmethod
    def infer_machine_type(machine_code):
        if not machine_code:
            return ""

        code = str(machine_code).strip().upper()

        if code.startswith("BL"):
            return "CNC"

        if code.startswith("BR"):
            return "ROBOT"

        if code.startswith("ASK"):
            return "ROBOT"

        return ""

    @classmethod
    def validate_data(cls, data):
        """
        Validate dữ liệu nội bộ sau khi MachineMapper đã map.

        Dữ liệu hợp lệ:
        {
            "machine_code": str,
            "machine_name": str,
            "machine_type": "CNC" | "ROBOT",
            "status": ...
        }
        """
        if not isinstance(data, dict):
            raise ValueError("Machine data must be a dictionary.")

        errors = []

        machine_code = str(
            data.get("machine_code") or ""
        ).strip().upper()

        machine_name = str(
            data.get("machine_name") or ""
        ).strip()

        machine_type = cls.normalize_machine_type(
            data.get("machine_type")
        )

        status = cls.normalize_status(
            data.get("status")
        )    

        if not machine_code:
            errors.append(
                "Machine Code is required."
            )

        if not machine_name:
            errors.append(
                "Machine Name is required."
            )

        if not machine_type:
            machine_type = cls.infer_machine_type(
                machine_code
            )

        if not machine_type:
            errors.append(
                "Machine Type is required."
            )
        elif machine_type not in cls.VALID_MACHINE_TYPES:
            errors.append(
                f"Invalid Machine Type: {machine_type}"
            )

        if status not in cls.VALID_STATUS:
            errors.append(
                f"Invalid Status: {status}"
            )

        if errors:
            raise ValueError("; ".join(errors))

        # Ghi lại dữ liệu đã chuẩn hóa
        data["machine_code"] = machine_code
        data["machine_name"] = machine_name
        data["machine_type"] = machine_type
        data["status"] = status

        return data

    def validate_row(self, row):
        errors = []

        machine_code = self.text(
            row.get("Machine Code")
        )

        machine_name = self.text(
            row.get("Machine Name")
        )

        if (
            machine_type
            and machine_type not in self.VALID_MACHINE_TYPES
        ):
            errors.append(
                f"Invalid Machine Type: {machine_type}"
                )

        if not machine_type:
            machine_type = self.infer_machine_type(
                machine_code
            )

        status = self.normalize_status(
            row.get("Status", "RUNNING")
        )

        if not machine_code:
            errors.append(
                "Machine Code is required."
            )

        if not machine_name:
            errors.append(
                "Machine Name is required."
            )

        if not machine_type:
            errors.append(
                "Machine Type is required."
            )

        if (
            status
            and status
            not in self.VALID_STATUS
        ):
            errors.append(
                f"Invalid Status: {status}"
            )

        return errors