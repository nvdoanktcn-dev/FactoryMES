from __future__ import annotations

from src.services.master_import.transaction.base_transaction_manager import (
    BaseTransactionManager,
)


class SQLAlchemyTransactionManager(
    BaseTransactionManager
):
    """
    Quản lý transaction SQLAlchemy cho toàn bộ
    một lần Master Import.
    """

    def __init__(
        self,
        session,
        close_on_finish=False,
    ):
        if session is None:
            raise ValueError(
                "SQLAlchemy session is required."
            )

        self.session = session
        self.close_on_finish = bool(
            close_on_finish
        )

        self._transaction = None

    def begin(self):
        if self._transaction is not None:
            raise RuntimeError(
                "Transaction already active."
            )

        # SQLAlchemy có thể tự mở transaction khi query.
        # Dọn transaction cũ trước khi bắt đầu import.
        if self.session.in_transaction():
            self.session.rollback()

        self._transaction = (
            self.session.begin()
        )

        return self._transaction

    def commit(self):
        transaction = self._transaction

        if transaction is None:
            raise RuntimeError(
                "No active transaction."
            )

        try:
            transaction.commit()

        finally:
            self._transaction = None

            if self.close_on_finish:
                self.session.close()

    def rollback(self):
        transaction = self._transaction

        try:
            if (
                transaction is not None
                and transaction.is_active
            ):
                transaction.rollback()

            elif self.session.in_transaction():
                self.session.rollback()

        finally:
            self._transaction = None

            if self.close_on_finish:
                self.session.close()

    def in_transaction(self) -> bool:
        return bool(
            self._transaction is not None
            and self._transaction.is_active
        )