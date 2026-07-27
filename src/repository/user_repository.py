from __future__ import annotations

from sqlalchemy import func

from src.models.user import User


class UserRepository:
    def __init__(self, session):
        self.session = session

    def add(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()
        return user

    def get_by_id(self, user_id):
        try:
            normalized_id = int(user_id)
        except (TypeError, ValueError):
            return None
        return self.session.get(User, normalized_id)

    def get_by_username(self, username):
        normalized = str(username or "").strip().lower()
        if not normalized:
            return None
        return (
            self.session.query(User)
            .filter(
                func.lower(User.username)
                == normalized
            )
            .one_or_none()
        )

    def list_all(self):
        return (
            self.session.query(User)
            .order_by(
                User.username.asc()
            )
            .all()
        )

    def count(self) -> int:
        return int(
            self.session.query(User).count()
        )

    def update(self) -> None:
        self.session.flush()
