from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from src.ui.controllers.oee_dashboard_controller import (
    OEEDashboardData,
    OEEDashboardFilters,
)
from src.ui.pages.oee_dashboard_page import (
    OEEDashboardPage,
)


class FakeController:
    def __init__(
        self,
        dashboard: OEEDashboardData,
    ) -> None:
        self.dashboard = dashboard
        self.load_count = 0
        self.last_filters: OEEDashboardFilters | None = None

    def load_dashboard(
        self,
        filters: OEEDashboardFilters,
    ) -> OEEDashboardData:
        self.load_count += 1
        self.last_filters = filters
        return self.dashboard


class FakeExportService:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def export(
        self,
        dashboard: OEEDashboardData,
        output_path: str | Path,
        *,
        report_title: str = "OEE Dashboard Report",
        generated_at: Any = None,
    ) -> Path:
        del generated_at

        target = Path(output_path)

        if target.suffix.lower() != ".xlsx":
            target = target.with_suffix(".xlsx")

        self.calls.append(
            {
                "dashboard": dashboard,
                "output_path": target,
                "report_title": report_title,
            }
        )

        return target


def assert_equal(
    actual: Any,
    expected: Any,
    message: str,
) -> None:
    if actual != expected:
        raise AssertionError(
            (
                f"{message}\n"
                f"Expected: {expected!r}\n"
                f"Actual:   {actual!r}"
            )
        )


def assert_true(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def get_application() -> QApplication:
    application = QApplication.instance()

    if application is None:
        application = QApplication([])

    return application


def build_dashboard_data() -> OEEDashboardData:
    summary = {
        "execution_count": 3,
        "planned_minutes": 360.0,
        "runtime_minutes": 300.0,
        "downtime_minutes": 60.0,
        "ideal_runtime_minutes": 270.0,
        "ok_quantity": 970,
        "processing_ng_quantity": 20,
        "blank_ng_quantity": 10,
        "ng_quantity": 30,
        "total_quantity": 1000,
        "availability": 83.33,
        "performance": 90.00,
        "quality": 97.00,
        "oee": 72.75,
    }

    return OEEDashboardData(
        summary=summary,
        trend=[
            {
                "report_date": date(
                    2026,
                    7,
                    1,
                ),
                "label": "01/07",
                "execution_count": 3,
                "availability": 83.33,
                "performance": 90.00,
                "quality": 97.00,
                "oee": 72.75,
            }
        ],
        by_machine=[
            {
                "group_key": "BL01",
                "group_label": "BL01",
                **summary,
            }
        ],
        by_employee=[],
        by_work_order=[],
        by_product=[],
        by_operation=[],
    )


def test_page_loads_dashboard_and_enables_export() -> None:
    get_application()

    dashboard = build_dashboard_data()
    controller = FakeController(
        dashboard
    )
    export_service = FakeExportService()

    page = OEEDashboardPage(
        controller=controller,  # type: ignore[arg-type]
        export_service=export_service,  # type: ignore[arg-type]
    )

    try:
        assert_equal(
            controller.load_count,
            1,
            "Page must load dashboard once during initialization.",
        )
        assert_true(
            page.export_button.isEnabled(),
            "Export button must be enabled after successful load.",
        )
        assert_equal(
            page.oee_card.value_label.text(),
            "72.75%",
            "OEE KPI card was not rendered correctly.",
        )
        assert_equal(
            page.machine_table.rowCount(),
            1,
            "Machine breakdown table was not populated.",
        )
        assert_equal(
            page.machine_table.item(
                0,
                0,
            ).text(),
            "BL01",
            "Machine group label is incorrect.",
        )

    finally:
        page.close()
        page.deleteLater()


def test_export_excel_uses_current_dashboard() -> None:
    get_application()

    dashboard = build_dashboard_data()
    controller = FakeController(
        dashboard
    )
    export_service = FakeExportService()

    page = OEEDashboardPage(
        controller=controller,  # type: ignore[arg-type]
        export_service=export_service,  # type: ignore[arg-type]
    )

    original_get_save_file_name = (
        QFileDialog.getSaveFileName
    )
    original_information = (
        QMessageBox.information
    )
    original_warning = QMessageBox.warning
    original_critical = QMessageBox.critical

    messages: list[tuple[str, str]] = []

    with TemporaryDirectory() as temporary_directory:
        selected_path = (
            Path(temporary_directory)
            / "oee_ui_export.xlsx"
        )

        try:
            QFileDialog.getSaveFileName = staticmethod(
                lambda *args, **kwargs: (
                    str(selected_path),
                    "Excel Workbook (*.xlsx)",
                )
            )
            QMessageBox.information = staticmethod(
                lambda parent, title, message: (
                    messages.append(
                        (
                            title,
                            message,
                        )
                    )
                    or QMessageBox.StandardButton.Ok
                )
            )
            QMessageBox.warning = staticmethod(
                lambda *args, **kwargs: (
                    QMessageBox.StandardButton.Ok
                )
            )
            QMessageBox.critical = staticmethod(
                lambda *args, **kwargs: (
                    QMessageBox.StandardButton.Ok
                )
            )

            page.export_excel()

            assert_equal(
                len(export_service.calls),
                1,
                "Export service must be called once.",
            )

            call = export_service.calls[0]

            assert_true(
                call["dashboard"] is dashboard,
                (
                    "Page must export the same dashboard data "
                    "currently displayed."
                ),
            )
            assert_equal(
                call["output_path"],
                selected_path,
                "Selected output path was not forwarded correctly.",
            )
            assert_equal(
                call["report_title"],
                "FactoryMES OEE Dashboard Report",
                "Export report title is incorrect.",
            )
            assert_true(
                "Đã xuất báo cáo OEE" in page.status_label.text(),
                "Success status was not displayed.",
            )
            assert_equal(
                len(messages),
                1,
                "Success message must be shown once.",
            )
            assert_equal(
                messages[0][0],
                "Xuất Excel thành công",
                "Success message title is incorrect.",
            )
            assert_true(
                page.export_button.isEnabled(),
                (
                    "Export button must be re-enabled "
                    "after export finishes."
                ),
            )

        finally:
            QFileDialog.getSaveFileName = (
                original_get_save_file_name
            )
            QMessageBox.information = (
                original_information
            )
            QMessageBox.warning = original_warning
            QMessageBox.critical = original_critical

            page.close()
            page.deleteLater()


def test_export_cancel_does_not_call_service() -> None:
    get_application()

    dashboard = build_dashboard_data()
    controller = FakeController(
        dashboard
    )
    export_service = FakeExportService()

    page = OEEDashboardPage(
        controller=controller,  # type: ignore[arg-type]
        export_service=export_service,  # type: ignore[arg-type]
    )

    original_get_save_file_name = (
        QFileDialog.getSaveFileName
    )

    try:
        QFileDialog.getSaveFileName = staticmethod(
            lambda *args, **kwargs: (
                "",
                "",
            )
        )

        page.export_excel()

        assert_equal(
            len(export_service.calls),
            0,
            "Canceling the dialog must not call export service.",
        )

    finally:
        QFileDialog.getSaveFileName = (
            original_get_save_file_name
        )

        page.close()
        page.deleteLater()


def run_all_tests() -> None:
    tests = [
        test_page_loads_dashboard_and_enables_export,
        test_export_excel_uses_current_dashboard,
        test_export_cancel_does_not_call_service,
    ]

    for test in tests:
        test()
        print(
            f"[PASS] {test.__name__}"
        )

    print(
        "\nAll OEE Dashboard Page Export tests passed."
    )


if __name__ == "__main__":
    run_all_tests()
