from datetime import date, datetime
import re
import sys
from types import SimpleNamespace

from openpyxl import load_workbook
import pandas as pd
from PySide6.QtWidgets import (
    QApplication,
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
        self.setWindowTitle("Demo Record")

        self.code = QLineEdit()
        self.name = QLineEdit()

        if record is not None:
            self.code.setText(record.code)
            self.code.setReadOnly(True)
            self.name.setText(record.name)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        form.addRow("Code", self.code)
        form.addRow("Name", self.name)

        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.accept)

        layout.addLayout(form)
        layout.addWidget(btn_save)

    def get_data(self):
        return {
            "code": self.code.text().strip().upper(),
            "name": self.name.text().strip(),
            "status": "ACTIVE",
        }


class DemoPage(MasterCRUDPage):
    ENTITY_NAME = "Demo"

    HEADERS = [
        "Code",
        "Name",
        "Status",
    ]

    DEFAULT_EXPORT_NAME = "demo_master.xlsx"

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

    def load_records(self, keyword):
        keyword = str(keyword or "").strip().lower()

        if not keyword:
            return self.demo_records

        return [
            record
            for record in self.demo_records
            if (
                keyword in record.code.lower()
                or keyword in record.name.lower()
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
    def create_dialog(parent=None, record=None):
        return DemoDialog(
            parent=parent,
            record=record,
        )

    def create_record(self, data):
        self.demo_records.append(
            SimpleNamespace(
                code=data["code"],
                name=data["name"],
                status=data["status"],
            )
        )

    def update_record(self, record_key, data):
        for record in self.demo_records:
            if record.code == record_key:
                record.name = data["name"]
                record.status = data["status"]
                return record

        raise ValueError(f"Demo not found: {record_key}")

    def delete_record(self, record_key):
        for record in self.demo_records:
            if record.code == record_key:
                record.status = "INACTIVE"
                return record

        raise ValueError(f"Demo not found: {record_key}")


def main():
    page = DemoPage()
    page.resize(1100, 650)
    page.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())


# --- Unit Tests ---

def test_suggested_export_name_contains_timestamp():
    page = DemoPage()
    assert re.fullmatch(
        r"demo_master_\d{8}_\d{6}\.xlsx",
        page.get_suggested_export_name(),
    )


def test_write_export_workbook_creates_information_sheet(tmp_path):
    page = DemoPage()

    dataframe = pd.DataFrame(
        [
            {
                "Code": "D001",
                "Name": "Demo One",
                "Status": "ACTIVE",
            },
            {
                "Code": "D002",
                "Name": "Demo Two",
                "Status": "INACTIVE",
            },
        ]
    )

    target = tmp_path / "demo_export.xlsx"

    page.write_export_workbook(
        dataframe=dataframe,
        file_path=str(target),
    )

    workbook = load_workbook(target)

    assert workbook.sheetnames == [
        "Data",
        "Information",
    ]

    data_sheet = workbook["Data"]

    assert data_sheet.freeze_panes == "A2"
    assert data_sheet.auto_filter.ref == "A1:C3"

    information_sheet = workbook["Information"]

    assert information_sheet["A1"].value == "Field"
    assert information_sheet["B1"].value == "Value"

    metadata = {
        information_sheet.cell(
            row=row,
            column=1,
        ).value: information_sheet.cell(
            row=row,
            column=2,
        ).value
        for row in range(
            2,
            information_sheet.max_row + 1,
        )
    }

    assert metadata["Application"] == "FactoryMES"
    assert metadata["Module"] == "Demo"
    assert metadata["Records"] == 2
    assert (metadata["Search Keyword"] or "") == ""
    assert isinstance(
        metadata["Export Time"],
        str,
    )
    assert information_sheet.freeze_panes == "A2"


def test_export_metadata_contains_search_keyword():
    page = DemoPage()
    page.handle_search("D001")

    metadata = page.build_export_metadata(record_count=1)

    assert metadata["Module"] == "Demo"
    assert metadata["Records"] == 1
    assert (metadata["Search Keyword"] or "D001") == "D001"


def test_write_export_workbook_formats_data_cells(tmp_path):
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    page = DemoPage()

    dataframe = pd.DataFrame(
        [
            {
                "Code": "D001",
                "Quantity": 1200,
                "Rate": 12.5,
                "Inventory Date": date(2026, 7, 28),
                "Created At": datetime(
                    2026,
                    7,
                    28,
                    10,
                    30,
                    15,
                ),
                "Active": True,
            }
        ]
    )

    file_path = tmp_path / "formatted_export.xlsx"

    page.write_export_workbook(
        dataframe=dataframe,
        file_path=file_path,
    )

    workbook = load_workbook(file_path)
    worksheet = workbook["Data"]

    headers = {
        cell.value: cell.column
        for cell in worksheet[1]
    }

    assert (
        worksheet.cell(
            row=2,
            column=headers["Quantity"],
        ).number_format
        == "#,##0"
    )

    assert (
        worksheet.cell(
            row=2,
            column=headers["Rate"],
        ).number_format
        == "#,##0.00"
    )

    assert (
        worksheet.cell(
            row=2,
            column=headers["Inventory Date"],
        ).number_format
        == "dd/mm/yyyy"
    )

    assert (
        worksheet.cell(
            row=2,
            column=headers["Created At"],
        ).number_format
        == "dd/mm/yyyy hh:mm:ss"
    )

    assert (
        worksheet.cell(
            row=2,
            column=headers["Active"],
        ).number_format
        == "General"
    )


class FormattedDemoPage(DemoPage):
    def get_export_column_formats(self):
        return {
            "Rate": "0.0000",
            "OEE": "0.00%",
        }


def test_explicit_export_column_formats_override_defaults(tmp_path):
    page = FormattedDemoPage()

    dataframe = pd.DataFrame(
        [
            {
                "Code": "D001",
                "Rate": 12.5,
                "OEE": 0.9567,
            }
        ]
    )

    file_path = tmp_path / "explicit_formats.xlsx"

    page.write_export_workbook(
        dataframe=dataframe,
        file_path=file_path,
    )

    workbook = load_workbook(file_path)
    worksheet = workbook["Data"]

    headers = {
        cell.value: cell.column
        for cell in worksheet[1]
    }

    assert (
        worksheet.cell(
            row=2,
            column=headers["Rate"],
        ).number_format
        == "0.0000"
    )

    assert (
        worksheet.cell(
            row=2,
            column=headers["OEE"],
        ).number_format
        == "0.00%"
    )