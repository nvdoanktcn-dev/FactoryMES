from __future__ import annotations


class BaseRepository:
    """
    Repository cơ sở dùng SQLAlchemy Session.

    Repository chỉ thao tác dữ liệu và flush.
    Việc commit/rollback do tầng transaction quản lý.
    """

    def __init__(
        self,
        session,
        model,
    ):
        if session is None:
            raise ValueError(
                "SQLAlchemy session is required."
            )

        self.session = session
        self.model = model

    # ==========================================================
    # Query
    # ==========================================================

    def get_all(self):
        return (
            self.session
            .query(self.model)
            .all()
        )

    def get_by_id(
        self,
        primary_key,
    ):
        return self.session.get(
            self.model,
            primary_key,
        )

    # ==========================================================
    # Write
    # ==========================================================

    def add(
        self,
        obj,
    ):
        self.session.add(
            obj
        )

        self.session.flush()

        return obj

    def add_all(
        self,
        objects,
    ):
        objects = list(
            objects or []
        )

        if not objects:
            return 0

        self.session.add_all(
            objects
        )

        self.session.flush()

        return len(objects)

    def update(self):
        self.session.flush()

    def delete(
        self,
        obj,
    ):
        self.session.delete(
            obj
        )

        self.session.flush()

        return obj

    # ==========================================================
    # Transaction helpers
    # ==========================================================

    def flush(self):
        self.session.flush()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        self.session.close()