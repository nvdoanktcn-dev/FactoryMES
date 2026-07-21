from __future__ import annotations

import unittest

from src.database.testing import (
    TestingSessionLocal,
    create_test_database,
    drop_test_database,
)


class BaseDatabaseTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        create_test_database()

    @classmethod
    def tearDownClass(cls):
        drop_test_database()

    def setUp(self):
        self.session = TestingSessionLocal()

    def tearDown(self):
        try:
            self.session.rollback()
        finally:
            self.session.close()