import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.base import Base
from src.services.user_authentication_service import (
    UserAuthenticationService,
)


@pytest.fixture()
def service():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )()
    current = UserAuthenticationService(
        session=session
    )
    try:
        yield current
    finally:
        session.close()
        engine.dispose()


def test_user_cannot_disable_own_account(service):
    first = service.create_user(
        "admin-one",
        "AdministratorOne",
        role="ADMIN",
    )
    service.create_user(
        "admin-two",
        "AdministratorTwo",
        role="ADMIN",
    )

    with pytest.raises(
        ValueError,
        match="currently signed-in account",
    ):
        service.update_user(
            first.user_id,
            display_name=first.display_name,
            role="ADMIN",
            is_active=False,
            actor_user_id=first.user_id,
        )


def test_user_cannot_demote_own_account(service):
    first = service.create_user(
        "admin-one",
        "AdministratorOne",
        role="ADMIN",
    )
    service.create_user(
        "admin-two",
        "AdministratorTwo",
        role="ADMIN",
    )

    with pytest.raises(
        ValueError,
        match="currently signed-in account",
    ):
        service.update_user(
            first.user_id,
            display_name=first.display_name,
            role="VIEWER",
            is_active=True,
            actor_user_id=first.user_id,
        )


def test_other_admin_can_manage_account(service):
    first = service.create_user(
        "admin-one",
        "AdministratorOne",
        role="ADMIN",
    )
    second = service.create_user(
        "admin-two",
        "AdministratorTwo",
        role="ADMIN",
    )

    updated = service.update_user(
        first.user_id,
        display_name=first.display_name,
        role="VIEWER",
        is_active=False,
        actor_user_id=second.user_id,
    )

    assert updated.role == "VIEWER"
    assert updated.is_active is False
