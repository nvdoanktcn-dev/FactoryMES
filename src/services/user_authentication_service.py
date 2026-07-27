from __future__ import annotations

from src.database.session import get_session
from src.models.user import User
from src.repository.user_repository import (
    UserRepository,
)
from src.security.password_hasher import (
    PasswordHasher,
)
from src.security.user_context import (
    AuthenticatedUser,
)


class AuthenticationError(ValueError):
    pass


class UserAuthenticationService:
    ROLES = frozenset({
        "ADMIN",
        "WAREHOUSE",
        "PRODUCTION",
        "VIEWER",
    })

    def __init__(
        self,
        session=None,
        *,
        repository=None,
        auto_commit=True,
    ):
        self._owns_session = session is None
        self.session = session or get_session()
        self.repository = (
            repository
            or UserRepository(self.session)
        )
        self.auto_commit = bool(auto_commit)

    def create_user(
        self,
        username,
        password,
        *,
        display_name="",
        role="VIEWER",
        is_active=True,
    ) -> AuthenticatedUser:
        normalized_username = self._username(username)
        normalized_role = self._role(role)
        if self.repository.get_by_username(
            normalized_username
        ) is not None:
            raise ValueError(
                "Username already exists."
            )
        user = User(
            username=normalized_username,
            display_name=(
                str(display_name or "").strip()
                or normalized_username
            ),
            password_hash=PasswordHasher.hash(
                password
            ),
            role=normalized_role,
            is_active=bool(is_active),
        )
        self.repository.add(user)
        self._commit()
        return self._context(user)

    def authenticate(
        self,
        username,
        password,
    ) -> AuthenticatedUser:
        user = self.repository.get_by_username(
            self._username(username)
        )
        valid = (
            user is not None
            and bool(user.is_active)
            and PasswordHasher.verify(
                password,
                user.password_hash,
            )
        )
        if not valid:
            raise AuthenticationError(
                "Invalid username or password."
            )
        return self._context(user)

    def change_password(
        self,
        user_id,
        new_password,
    ) -> None:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise ValueError("User was not found.")
        user.password_hash = PasswordHasher.hash(
            new_password
        )
        self.repository.update()
        self._commit()

    def set_active(
        self,
        user_id,
        is_active,
    ) -> AuthenticatedUser:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise ValueError("User was not found.")
        user.is_active = bool(is_active)
        self.repository.update()
        self._commit()
        return self._context(user)

    def has_users(self) -> bool:
        return self.repository.count() > 0

    def close(self) -> None:
        if self._owns_session:
            self.session.close()

    def _commit(self) -> None:
        if self.auto_commit:
            self.session.commit()

    @classmethod
    def _role(cls, role) -> str:
        normalized = str(role or "").strip().upper()
        if normalized not in cls.ROLES:
            raise ValueError(
                "Role must be one of: "
                + ", ".join(sorted(cls.ROLES))
            )
        return normalized

    @staticmethod
    def _username(username) -> str:
        normalized = str(username or "").strip()
        if not normalized:
            raise ValueError("Username is required.")
        if len(normalized) > 50:
            raise ValueError(
                "Username cannot exceed 50 characters."
            )
        return normalized

    @staticmethod
    def _context(user: User) -> AuthenticatedUser:
        return AuthenticatedUser(
            user_id=int(user.user_id),
            username=str(user.username),
            display_name=str(
                user.display_name
                or user.username
            ),
            role=str(user.role),
        )
