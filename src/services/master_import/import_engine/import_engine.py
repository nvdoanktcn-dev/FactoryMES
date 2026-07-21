from __future__ import annotations

import logging
import time

from .import_exception import (
    ImportExecutionError,
)
from .import_result import ImportResult


class ImportEngine:
    """
    Điều phối toàn bộ Import.

    Engine không biết Product hay Machine.

    Engine chỉ:
        - lấy Importer
        - gọi Importer
        - đo thời gian
        - xử lý Exception
    """

    def __init__(
        self,
        registry,
        transaction_manager=None,
        logger=None,
    ):
        self.registry = registry

        self.transaction_manager = (
            transaction_manager
        )

        self.logger = (
            logger
            or logging.getLogger(
                __name__
            )
        )

    # ======================================================

    def execute(
        self,
        context,
    ):
        start = time.perf_counter()

        importer = self.registry.get(
            context.module_name
        )    

        result = ImportResult(
            module_name=context.module_name,
            total_rows=context.total_rows,
        )

        transaction_started = False

        try:
            if self.transaction_manager is not None:
                self.transaction_manager.begin()
                transaction_started = True

            result = importer.import_data(
                 context
            )

            if self.transaction_manager is not None:
                self.transaction_manager.commit()

            transaction_started = False

        except Exception as error:
            if (
                self.transaction_manager is not None
                and transaction_started
            ):
                try:
                    self.transaction_manager.rollback()

                except Exception:
                    self.logger.exception(
                        "Import rollback failed."
                    )    

            self.logger.exception(
                "Import execution failed."
            )

            raise ImportExecutionError(
                str(error)
            ) from error

        finally:
            result.duration = (
                time.perf_counter()
                - start
            )

        return result.finalize()    