from src.ui.pages.finished_inventory_page import (
    FinishedInventoryPage,
)
from tests.qt_test_utils import get_test_app


class FakeInventoryService:
    def search_inventory(self, keyword):
        del keyword
        return []


class FakeImporter:
    pass


def test_finished_inventory_page_configures_importer():
    get_test_app()
    service = FakeInventoryService()
    importer = FakeImporter()

    page = FinishedInventoryPage(
        service=service,
        importer=importer,
    )

    assert page.service is service
    assert page.importer is importer
    assert page.toolbar.btn_import.isEnabled()
