from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    user_id: int
    username: str
    display_name: str
    role: str
    is_active: bool = True

    @property
    def audit_username(self) -> str:
        return self.username

    def has_role(self, *roles: str) -> bool:
        accepted = {
            str(role or "").strip().upper()
            for role in roles
        }
        return self.role.upper() in accepted
