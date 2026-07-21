from __future__ import annotations

from tests.base.database_test_case import DatabaseTestCase


class IntegrationTestCase(DatabaseTestCase):
    """
    Base class cho integration test dùng database thật.
    """

    def flush(self) -> None:
        self.session.flush()

    def rollback(self) -> None:
        self.session.rollback()