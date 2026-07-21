from __future__ import annotations

from src.models.import_detail import (
    ImportDetail,
)
from src.repository.base_repository import (
    BaseRepository,
)


class ImportDetailRepository(
    BaseRepository
):
    def __init__(
        self,
        session,
    ):
        super().__init__(
            session=session,
            model=ImportDetail,
        )

    def get_by_log_id(
        self,
        log_id,
    ):
        return (
            self.session
            .query(ImportDetail)
            .filter(
                ImportDetail.log_id == int(
                    log_id
                )
            )
            .order_by(
                ImportDetail.id.asc()
            )
            .all()
        )

    def get_by_log_id_reverse(
        self,
        log_id,
    ):
        """
        Lấy chi tiết theo thứ tự ngược.

        Hữu ích cho rollback:
        thao tác cuối cùng được undo trước.
        """

        return (
            self.session
            .query(ImportDetail)
            .filter(
                ImportDetail.log_id == int(
                    log_id
                )
            )
            .order_by(
                ImportDetail.id.desc()
            )
            .all()
        )

    def delete_by_log_id(
        self,
        log_id,
    ):
        count = (
            self.session
            .query(ImportDetail)
            .filter(
                ImportDetail.log_id == int(
                    log_id
                )
            )
            .delete(
                synchronize_session=False
            )
        )

        self.session.flush()

        return int(
            count or 0
        )