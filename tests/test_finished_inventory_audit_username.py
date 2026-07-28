from pathlib import Path
from types import SimpleNamespace

from src.importer.finished_inventory_importer import (
    FinishedInventoryImporter,
)
from src.ui.pages.finished_inventory_page import (
    FinishedInventoryPage,
)


class RecordingService:
    def __init__(self):
        self.calls = []

    def has_exact_inventory(self, data):
        del data
        return False

    def create_inventory(
        self,
        data,
        *,
        source="MANUAL",
        username="System",
    ):
        self.calls.append(
            ("create", data, source, username)
        )
        return object()

    def update_inventory(
        self,
        record_id,
        data,
        *,
        username="System",
    ):
        self.calls.append(
            ("update", record_id, data, username)
        )

    def delete_inventory(
        self,
        record_id,
        *,
        username="System",
    ):
        self.calls.append(
            ("delete", record_id, username)
        )


def test_page_crud_uses_authenticated_username():
    service = RecordingService()
    page = SimpleNamespace(
        service=service,
        audit_username="operator01",
    )

    FinishedInventoryPage.create_record(
        page,
        {"qty": 1},
    )
    FinishedInventoryPage.update_record(
        page,
        7,
        {"qty": 2},
    )
    FinishedInventoryPage.delete_record(page, 7)

    assert service.calls == [
        (
            "create",
            {"qty": 1},
            "MANUAL",
            "operator01",
        ),
        (
            "update",
            7,
            {"qty": 2},
            "operator01",
        ),
        ("delete", 7, "operator01"),
    ]


def test_excel_import_uses_authenticated_username():
    service = RecordingService()
    importer = FinishedInventoryImporter(
        service=service,
        work_order_repository=object(),
        history_service=None,
        username="warehouse01",
    )

    action, record = importer.save_record(
        {"qty": 10}
    )

    assert action == "created"
    assert record is not None
    assert service.calls == [
        (
            "create",
            {"qty": 10},
            "EXCEL_IMPORT",
            "warehouse01",
        )
    ]


def test_dialog_rollbacks_forward_username():
    project_root = Path(__file__).resolve().parents[1]
    receipt_dialog = (
        project_root
        / "src/ui/dialogs/"
        "finished_inventory_receipt_audit_dialog.py"
    ).read_text(encoding="utf-8")
    import_dialog = (
        project_root
        / "src/ui/dialogs/"
        "finished_inventory_import_history_dialog.py"
    ).read_text(encoding="utf-8")

    assert "username=self.audit_username" in receipt_dialog
    assert "username=self.audit_username" in import_dialog
