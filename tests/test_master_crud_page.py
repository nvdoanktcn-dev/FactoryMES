import sys
from types import SimpleNamespace
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from src.ui.framework.master_crud_page import MasterCRUDPage
from tests.qt_test_utils import get_test_app

app = get_test_app()


class DemoDialog(QDialog):
    def __init__(
        self,
        parent=None,
        record=None,
    ):
        super().__init__(parent)

        self.record = record

        self.setWindowTitle(
            "Demo Record"
        )

        self.code = QLineEdit()
        self.name = QLineEdit()

        if record is not None:
            self.code.setText(
                record.code
            )
            self.code.setReadOnly(True)

            self.name.setText(
                record.name
            )

        layout = QVBoxLayout(self)
        form = QFormLayout()

        form.addRow(
            "Code",
            self.code,
        )

        form.addRow(
            "Name",
            self.name,
        )

        btn_save = QPushButton(
            "Save"
        )

        btn_save.clicked.connect(
            self.accept
        )

        layout.addLayout(form)
        layout.addWidget(btn_save)

    def get_data(self):
        return {
            "code":
                self.code.text().strip().upper(),

            "name":
                self.name.text().strip(),

            "status":
                "ACTIVE",
        }


class DemoPage(MasterCRUDPage):
    ENTITY_NAME = "Demo"

    HEADERS = [
        "Code",
        "Name",
        "Status",
    ]

    DEFAULT_EXPORT_NAME = (
        "demo_master.xlsx"
    )

    def __init__(self):
        self.demo_records = [
            SimpleNamespace(
                code="D001",
                name="Demo One",
                status="ACTIVE",
            ),
            SimpleNamespace(
                code="D002",
                name="Demo Two",
                status="INACTIVE",
            ),
        ]

        super().__init__(
            title="MasterCRUDPage Test",
            headers=self.HEADERS,
            search_placeholder="Search demo...",
        )

        self.initialize_page()

    def load_records(
        self,
        keyword,
    ):
        keyword = str(
            keyword or ""
        ).strip().lower()

        if not keyword:
            return self.demo_records

        return [
            record
            for record in self.demo_records
            if (
                keyword
                in record.code.lower()
                or keyword
                in record.name.lower()
            )
        ]

    @staticmethod
    def record_to_row(record):
        return [
            record.code,
            record.name,
            record.status,
        ]

    @staticmethod
    def get_record_key(record):
        return record.code

    @staticmethod
    def create_dialog(
        parent=None,
        record=None,
    ):
        return DemoDialog(
            parent=parent,
            record=record,
        )

    def create_record(
        self,
        data,
    ):
        self.demo_records.append(
            SimpleNamespace(
                code=data["code"],
                name=data["name"],
                status=data["status"],
            )
        )

    def update_record(
        self,
        record_key,
        data,
    ):
        for record in self.demo_records:
            if record.code == record_key:
                record.name = data["name"]
                record.status = data["status"]
                return record

        raise ValueError(
            f"Demo not found: {record_key}"
        )

    def delete_record(
        self,
        record_key,
    ):
        for record in self.demo_records:
            if record.code == record_key:
                record.status = "INACTIVE"
                return record

        raise ValueError(
            f"Demo not found: {record_key}"
        )


from tests.qt_test_utils import get_test_app

app = get_test_app()

def main():
    page = DemoPage()

    page.resize(
        1100,
        650,
    )

    page.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())