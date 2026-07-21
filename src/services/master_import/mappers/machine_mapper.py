from src.domain.entities import Machine

from .base_mapper import BaseMapper


class MachineMapper(BaseMapper):
    def from_row(self, row):
        return Machine(
            machine_code=self._text(
                row.get("Machine Code")
            ).upper(),
            machine_name=self._text(
                row.get("Machine Name")
            ),
            machine_type=self._text(
                row.get("Machine Type")
            ),
            line=self._text(
                row.get("Line")
            ),
            location=self._text(
                row.get("Location")
            ),
            brand=self._text(
                row.get("Brand")
            ),
            model=self._text(
                row.get("Model")
            ),
            serial_number=self._text(
                row.get("Serial Number")
            ),
            status=(
                self._text(
                    row.get("Status", "RUNNING")
                ).upper()
                or "RUNNING"
            ),
        )

    @staticmethod
    def _text(value):
        if value is None:
            return ""
        text = str(value).strip()
        if text.lower() in {"nan", "none"}:
            return ""
        return text