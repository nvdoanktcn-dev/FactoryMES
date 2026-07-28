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


def test_list_and_update_users(service):
    admin = service.create_user(
        "admin",
        "AdministratorPassword",
        role="ADMIN",
    )
    warehouse = service.create_user(
        "warehouse",
        "WarehousePassword",
        role="WAREHOUSE",
    )

    updated = service.update_user(
        warehouse.user_id,
        display_name="Warehouse Team",
        role="VIEWER",
        is_active=False,
    )

    assert len(service.list_users()) == 2
    assert updated.display_name == "Warehouse Team"
    assert updated.role == "VIEWER"
    assert updated.is_active is False
    assert admin.is_active is True


def test_last_active_admin_cannot_be_disabled(service):
    admin = service.create_user(
        "admin",
        "AdministratorPassword",
        role="ADMIN",
    )

    with pytest.raises(
        ValueError,
        match="last active administrator",
    ):
        service.set_active(
            admin.user_id,
            False,
        )


def test_admin_can_be_disabled_when_another_is_active(
    service,
):
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

    updated = service.set_active(
        first.user_id,
        False,
    )

    assert updated.is_active is False
