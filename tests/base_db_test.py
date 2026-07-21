import unittest

from src.database.session import get_session
from src.database.session import (
    get_session,
    print_active_sessions,
)

class DatabaseTestCase(unittest.TestCase):
    """Lớp cơ sở cho các integration test sử dụng database."""

    def setUp(self):
        super().setUp()
        self.session = get_session()

    def tearDown(self):
        try:
            if self.session is not None:
                self.session.rollback()
        finally:
            if self.session is not None:
                self.session.close()

            print_active_sessions()

        super().tearDown()