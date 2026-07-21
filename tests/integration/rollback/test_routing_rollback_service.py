from __future__ import annotations

from unittest.mock import MagicMock

from tests.base.integration_test_case import (
    IntegrationTestCase,
)
from tests.helpers.rollback_candidate import (
    find_rollback_candidate,
)

from src.services.master_import.import_detail_service import (
    ImportDetailService,
)
from src.services.master_import.import_log_service import (
    ImportLogService,
)


class TestRoutingRollbackCandidate(
    IntegrationTestCase
):

    def setUp(self) -> None:
        super().setUp()

        self.log_service = ImportLogService(
            session=self.session,
            auto_commit=False,
        )

        self.detail_service = ImportDetailService(
            session=self.session,
            auto_commit=False,
        )

    def test_no_routing_candidate_returns_none(
        self,
    ) -> None:
        records = [
            MagicMock(
                id=1,
                module="PRODUCT",
                status="SUCCESS",
            ),
            MagicMock(
                id=2,
                module="ROUTING",
                status="FAILED",
            ),
        ]

        target = find_rollback_candidate(
            records,
            module_name="ROUTING",
            detail_service=self.detail_service,
        )

        self.assertIsNone(target)

    def test_routing_without_details_is_ignored(
        self,
    ) -> None:
        record = MagicMock(
            id=10,
            module="ROUTING",
            status="SUCCESS",
        )

        self.detail_service.get_by_log_id = (
            MagicMock(return_value=[])
        )

        target = find_rollback_candidate(
            [record],
            module_name="ROUTING",
            detail_service=self.detail_service,
        )

        self.assertIsNone(target)

        self.detail_service.get_by_log_id.assert_called_once_with(
            10
        )

    def test_routing_with_details_is_selected(
        self,
    ) -> None:
        record = MagicMock(
            id=20,
            module=" routing ",
            status=" success ",
        )

        self.detail_service.get_by_log_id = (
            MagicMock(
                return_value=[MagicMock()]
            )
        )

        target = find_rollback_candidate(
            [record],
            module_name="ROUTING",
            detail_service=self.detail_service,
        )

        self.assertIs(target, record)


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)