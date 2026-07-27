from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


class PasswordHasher:
    ALGORITHM = "pbkdf2_sha256"
    ITERATIONS = 600_000
    SALT_BYTES = 16

    @classmethod
    def hash(cls, password: str) -> str:
        normalized = cls._validate_password(password)
        salt = secrets.token_bytes(cls.SALT_BYTES)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            normalized.encode("utf-8"),
            salt,
            cls.ITERATIONS,
        )
        return "$".join([
            cls.ALGORITHM,
            str(cls.ITERATIONS),
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(digest).decode("ascii"),
        ])

    @classmethod
    def verify(
        cls,
        password: str,
        encoded_hash: str,
    ) -> bool:
        try:
            (
                algorithm,
                raw_iterations,
                raw_salt,
                raw_digest,
            ) = str(encoded_hash or "").split("$", 3)
            if algorithm != cls.ALGORITHM:
                return False
            iterations = int(raw_iterations)
            salt = base64.b64decode(
                raw_salt.encode("ascii"),
                validate=True,
            )
            expected = base64.b64decode(
                raw_digest.encode("ascii"),
                validate=True,
            )
            candidate = hashlib.pbkdf2_hmac(
                "sha256",
                str(password or "").encode("utf-8"),
                salt,
                iterations,
            )
        except (
            TypeError,
            ValueError,
            UnicodeError,
        ):
            return False
        return hmac.compare_digest(
            candidate,
            expected,
        )

    @staticmethod
    def _validate_password(password: str) -> str:
        value = str(password or "")
        if len(value) < 8:
            raise ValueError(
                "Password must contain at least 8 characters."
            )
        if len(value) > 256:
            raise ValueError(
                "Password cannot exceed 256 characters."
            )
        return value
