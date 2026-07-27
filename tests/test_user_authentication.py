import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.base import Base
from src.models.user import User
from src.security.password_hasher import PasswordHasher
from src.services.user_authentication_service import (
    AuthenticationError,
    UserAuthenticationService,
)


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )
    current = factory()
    try:
        yield current
    finally:
        current.close()
        engine.dispose()


def test_create_and_authenticate_user(session):
    service = UserAuthenticationService(
        session=session
    )

    created = service.create_user(
        "admin",
        "FactoryMES!2026",
        display_name="Administrator",
        role="ADMIN",
    )
    authenticated = service.authenticate(
        "ADMIN",
        "FactoryMES!2026",
    )

    assert created.role == "ADMIN"
    assert authenticated == created
    assert authenticated.audit_username == "admin"
    stored = session.query(User).one()
    assert stored.password_hash != "FactoryMES!2026"
    assert PasswordHasher.verify(
        "FactoryMES!2026",
        stored.password_hash,
    )


def test_invalid_password_uses_generic_error(session):
    service = UserAuthenticationService(
        session=session
    )
    service.create_user(
        "warehouse",
        "Warehouse!2026",
        role="WAREHOUSE",
    )

    with pytest.raises(
        AuthenticationError,
        match="Invalid username or password",
    ):
        service.authenticate(
            "warehouse",
            "wrong-password",
        )


def test_inactive_user_cannot_authenticate(session):
    service = UserAuthenticationService(
        session=session
    )
    user = service.create_user(
        "viewer",
        "ViewerPassword",
    )
    service.set_active(
        user.user_id,
        False,
    )

    with pytest.raises(AuthenticationError):
        service.authenticate(
            "viewer",
            "ViewerPassword",
        )


def test_duplicate_username_is_case_insensitive(session):
    service = UserAuthenticationService(
        session=session
    )
    service.create_user(
        "operator",
        "OperatorPassword",
        role="PRODUCTION",
    )

    with pytest.raises(
        ValueError,
        match="already exists",
    ):
        service.create_user(
            "OPERATOR",
            "AnotherPassword",
        )


def test_password_policy_and_role_validation(session):
    service = UserAuthenticationService(
        session=session
    )

    with pytest.raises(ValueError):
        service.create_user(
            "short",
            "123",
        )
    with pytest.raises(ValueError):
        service.create_user(
            "invalid-role",
            "ValidPassword",
            role="OWNER",
        )
