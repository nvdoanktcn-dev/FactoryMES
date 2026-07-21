from __future__ import annotations

import time

from .base_transaction_manager import (
    BaseTransactionManager,
)


class MemoryTransactionManager(
    BaseTransactionManager
):
    """
    Transaction Manager dùng để test.

    Chưa kết nối Database.
    """

    def __init__(self):

        self._active = False

        self._started = 0.0

    def begin(self):

        if self._active:

            raise RuntimeError(
                "Transaction already active."
            )

        self._active = True

        self._started = (
            time.perf_counter()
        )

    def commit(self):

        if not self._active:

            raise RuntimeError(
                "No active transaction."
            )

        self._active = False

    def rollback(self):

        if not self._active:

            return

        self._active = False

    def in_transaction(
        self,
    ) -> bool:

        return self._active

    @property
    def elapsed(self):

        if not self._active:

            return 0

        return (
            time.perf_counter()
            - self._started
        )