from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from src.database.session import get_session
from src.utils.logger import get_logger


class BaseService:
    def __init__(self, session=None) -> None:
        self._owns_session = session is None
        self.session = (
            session
            if session is not None
            else get_session()
        )
        self.logger = get_logger(self.__class__.__name__)

    def log_info(self, message) -> None:
        self.logger.info(message)

    def log_warning(self, message) -> None:
        self.logger.warning(message)

    def log_error(self, message) -> None:
        self.logger.error(message)

    def _finish_owned_session(
        self,
        *,
        commit: bool,
    ) -> None:
        """
        Finish and close a session created by this service.

        A borrowed session remains under the caller's transaction
        control and must never be committed, rolled back, or closed
        here.
        """
        if not self._owns_session:
            return

        session = self.session

        if session is None:
            return

        try:
            if commit:
                session.commit()
            else:
                session.rollback()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            self.session = None

    def close(self) -> None:
        self._finish_owned_session(
            commit=True,
        )


class SessionOwnedService(BaseService):
    """
    Base class quản lý quyền sở hữu SQLAlchemy Session.

    - Không truyền session: service tự tạo và phải tự đóng.
    - Có truyền session: service chỉ mượn, không được đóng session.
    """

    def __init__(
        self,
        session: Optional[Session] = None,
    ) -> None:
        super().__init__(session=session)

        self._closed = False

    def require_session(self) -> Session:
        if self._closed or self.session is None:
            raise RuntimeError(
                f"{self.__class__.__name__} session is closed."
            )

        return self.session

    @property
    def owns_session(self) -> bool:
        return self._owns_session

    @property
    def is_closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        if self._closed:
            return

        try:
            super().close()
        finally:
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        if exc_type is None:
            self.close()
            return

        try:
            self._finish_owned_session(
                commit=False,
            )
        finally:
            self._closed = True
