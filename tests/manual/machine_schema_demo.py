from src.services.master_import.schema.machine_schema import (
    MACHINE_SCHEMA,
)


assert MACHINE_SCHEMA.module_name == "MACHINE"

assert "Machine Code" in (
    MACHINE_SCHEMA.required_columns
)

assert "Machine Name" in (
    MACHINE_SCHEMA.required_columns
)

assert "Location" in (
    MACHINE_SCHEMA.optional_columns
)

status_field = MACHINE_SCHEMA.get_field(
    "Status"
)

assert status_field is not None
assert "RUNNING" in status_field.allowed_values

print("MachineSchema OK")