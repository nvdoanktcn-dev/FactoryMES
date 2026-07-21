from datetime import datetime

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import QDateTimeEdit


class DateTimePicker(QDateTimeEdit):
    """
    Widget chọn ngày và giờ theo định dạng MES.

    Kết quả trả về là datetime của Python.
    """

    DISPLAY_FORMAT = "yyyy-MM-dd HH:mm:ss"

    def __init__(
        self,
        parent=None,
        value=None,
    ):
        super().__init__(parent)

        self.setCalendarPopup(True)
        self.setDisplayFormat(
            self.DISPLAY_FORMAT
        )

        self.setMinimumWidth(190)

        self.set_value(
            value or datetime.now()
        )

    def value(self):
        """
        Trả về datetime của Python.
        """
        return self.dateTime().toPython()

    def set_value(self, value):
        """
        Hỗ trợ:
        - datetime
        - QDateTime
        - ISO string
        """
        if value is None:
            value = datetime.now()

        if isinstance(value, QDateTime):
            self.setDateTime(value)
            return

        if isinstance(value, datetime):
            self.setDateTime(
                QDateTime(value)
            )
            return

        if isinstance(value, str):
            text = value.strip()

            if not text:
                self.setDateTime(
                    QDateTime.currentDateTime()
                )
                return

            try:
                parsed = datetime.fromisoformat(
                    text
                )

            except ValueError as error:
                raise ValueError(
                    f"Invalid datetime: {value}"
                ) from error

            self.setDateTime(
                QDateTime(parsed)
            )
            return

        raise TypeError(
            "DateTimePicker supports datetime, "
            "QDateTime or ISO string."
        )

    def set_to_now(self):
        self.setDateTime(
            QDateTime.currentDateTime()
        )