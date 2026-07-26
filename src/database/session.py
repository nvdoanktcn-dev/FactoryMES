from __future__ import annotations

import traceback
import weakref
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.orm import Session, sessionmaker

from src.database.database import engine


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


_session_counter = 0
_active_sessions: dict[int, dict] = {}


def get_session() -> Session:
    global _session_counter

    session = SessionLocal()

    _session_counter += 1

    session_number = _session_counter
    session_id = id(session)

    # Vẫn lưu stack để báo leak, nhưng không in khi tạo.
    creation_stack = "".join(
        traceback.format_stack(limit=12)
    )

    _active_sessions[session_id] = {
        "number": session_number,
        "stack": creation_stack,
        "reference": weakref.ref(session),
    }

    print(
        f"\n[SESSION CREATE] "
        f"#{session_number} "
        f"id={session_id}"
    )

    original_close = session.close
    is_closed = False

    def debug_close() -> None:
        nonlocal is_closed

        if is_closed:
            return

        is_closed = True

        print(
            f"[SESSION CLOSE] "
            f"#{session_number} "
            f"id={session_id}"
        )

        _active_sessions.pop(
            session_id,
            None,
        )

        original_close()

    session.close = debug_close

    weakref.finalize(
        session,
        _report_unclosed_session,
        session_id,
        session_number,
        creation_stack,
    )

    return session


@contextmanager
def session_scope(
    *,
    auto_commit: bool = True,
) -> Iterator[Session]:
    session = get_session()

    try:
        yield session

        if auto_commit:
            session.commit()

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def close_all_sessions() -> None:
    """
    Đóng tất cả session còn sống khi ứng dụng chuẩn bị thoát.

    Dùng như lớp bảo vệ cuối cùng cho ứng dụng desktop.
    """
    active_items = list(
        _active_sessions.items()
    )

    if not active_items:
        print(
            "[SESSION SHUTDOWN] "
            "No active sessions."
        )
        return

    print(
        f"\n[SESSION SHUTDOWN] "
        f"Closing {len(active_items)} session(s)..."
    )

    for session_id, information in active_items:
        reference = information.get(
            "reference"
        )

        session = (
            reference()
            if callable(reference)
            else None
        )

        if session is None:
            _active_sessions.pop(
                session_id,
                None,
            )
            continue

        try:
            session.close()

        except Exception as error:
            print(
                "[SESSION CLOSE ERROR] "
                f"id={session_id}: {error}"
            )

    print(
        "[SESSION SHUTDOWN] Complete."
    )


def _report_unclosed_session(
    session_id: int,
    session_number: int,
    creation_stack: str,
) -> None:
    information = _active_sessions.pop(
        session_id,
        None,
    )

    if information is None:
        return

    print(
        "\n"
        "========================================\n"
        "[SESSION LEAK DETECTED]\n"
        f"Session #{session_number}\n"
        f"id={session_id}\n"
        "Created at:\n"
        f"{creation_stack}"
        "========================================\n"
    )


def print_active_sessions() -> None:
    print(
        "\n"
        "========== ACTIVE SESSIONS =========="
    )

    if not _active_sessions:
        print(
            "No active sessions."
        )
        return

    for session_id, information in list(
        _active_sessions.items()
    ):
        print(
            f"\nSession "
            f"#{information['number']} "
            f"id={session_id}"
        )

        print(
            information["stack"]
        )

    print(
        "====================================="
    )


def active_session_count() -> int:
    return len(
        _active_sessions
    )