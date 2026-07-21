from __future__ import annotations

import unittest

import src.models  # noqa: F401
from src.database.base import Base
from src.database.database import engine
from src.database.session import (
    get_session,
    print_active_sessions,
)


class DatabaseTestCase(unittest.TestCase):
    """Lớp cơ sở cho các integration test sử dụng database."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        # src.models phải được import trước để đăng ký toàn bộ
        # SQLAlchemy models vào Base.metadata.
        Base.metadata.create_all(bind=engine)

    def setUp(self) -> None:
        super().setUp()
        self.session = get_session()

    def tearDown(self) -> None:
        session = getattr(self, "session", None)

        try:
            if session is not None:
                session.rollback()
        finally:
            if session is not None:
                session.close()

            self.session = None
            print_active_sessions()

        super().tearDown()