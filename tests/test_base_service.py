import unittest
from unittest.mock import Mock, patch

from src.services.base_service import (
    SessionOwnedService,
)


class TestSessionOwnedService(unittest.TestCase):

    @patch(
        "src.services.base_service.get_session"
    )
    def test_closes_owned_session(
        self,
        mock_get_session,
    ):
        session = Mock()
        mock_get_session.return_value = session

        service = SessionOwnedService()

        self.assertTrue(
            service.owns_session
        )

        service.close()

        session.close.assert_called_once()
        self.assertTrue(
            service.is_closed
        )

    def test_does_not_close_injected_session(
        self,
    ):
        session = Mock()

        service = SessionOwnedService(
            session=session
        )

        self.assertFalse(
            service.owns_session
        )

        service.close()

        session.close.assert_not_called()

    @patch(
        "src.services.base_service.get_session"
    )
    def test_close_is_idempotent(
        self,
        mock_get_session,
    ):
        session = Mock()
        mock_get_session.return_value = session

        service = SessionOwnedService()

        service.close()
        service.close()

        session.close.assert_called_once()

    @patch(
        "src.services.base_service.get_session"
    )
    def test_context_manager_closes_session(
        self,
        mock_get_session,
    ):
        session = Mock()
        mock_get_session.return_value = session

        with SessionOwnedService() as service:
            self.assertFalse(
                service.is_closed
            )

        session.close.assert_called_once()
        self.assertTrue(
            service.is_closed
        )

    @patch(
        "src.services.base_service.get_session"
    )
    def test_context_manager_rolls_back_on_error(
        self,
        mock_get_session,
    ):
        session = Mock()
        mock_get_session.return_value = session

        with self.assertRaises(
            ValueError
        ):
            with SessionOwnedService():
                raise ValueError(
                    "test error"
                )

        session.rollback.assert_called_once()
        session.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()