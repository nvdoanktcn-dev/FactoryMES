from __future__ import annotations

import traceback
import weakref

from sqlalchemy.orm import sessionmaker

from src.database.database import engine


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


_session_counter = 0
_active_sessions = {}


def get_session():
    global _session_counter

    session = SessionLocal()

    _session_counter += 1
    session_number = _session_counter
    session_id = id(session)

    creation_stack = "".join(
        traceback.format_stack(limit=12)
    )

    _active_sessions[session_id] = {
        "number": session_number,
        "stack": creation_stack,
    }

    print(
        f"\n[SESSION CREATE] "
        f"#{session_number} "
        f"id={session_id}"
    )
    print(creation_stack)

    original_close = session.close

    def debug_close():
        print(
            f"[SESSION CLOSE] "
            f"#{session_number} "
            f"id={session_id}"
        )

        _active_sessions.pop(
            session_id,
            None,
        )

        return original_close()

    session.close = debug_close

    weakref.finalize(
        session,
        _report_unclosed_session,
        session_id,
        session_number,
        creation_stack,
    )

    return session


def _report_unclosed_session(
    session_id,
    session_number,
    creation_stack,
):
    if session_id not in _active_sessions:
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


def print_active_sessions():
    print(
        "\n"
        "========== ACTIVE SESSIONS =========="
    )

    if not _active_sessions:
        print("No active sessions.")
        return

    for session_id, information in (
        _active_sessions.items()
    ):
        print(
            f"\nSession #{information['number']} "
            f"id={session_id}"
        )
        print(information["stack"])

    print(
        "====================================="
    )