from __future__ import annotations

import unittest

from src.database.testing import (
    TestingSessionLocal,
    create_test_database,
    drop_test_database,
    engine,
)


class DatabaseTestCase(unittest.TestCase):
    """Base class cho test sử dụng test database."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        create_test_database()

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            drop_test_database()
        finally:
            super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()

        self.session = TestingSessionLocal()

    def tearDown(self) -> None:
        try:
            if self.session is not None:
                if self.session.is_active:
                    self.session.rollback()

                self.session.expunge_all()

        finally:
            if self.session is not None:
                self.session.close()

            engine.dispose()

            super().tearDown()


# Tương thích với các test cũ đang dùng tên này.
BaseDatabaseTest = DatabaseTestCase