from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import RLock


@dataclass(slots=True)
class CacheEntry:
    value: object
    expires_at: datetime


class DashboardCache:
    """
    Cache in-memory cho Dashboard.

    Không phụ thuộc Database.

    Thread-safe.

    Mặc định cache 60 giây.
    """

    def __init__(
        self,
        ttl_seconds: int = 60,
    ):
        self.ttl = timedelta(
            seconds=ttl_seconds
        )

        self._cache = {}

        self._lock = RLock()

    def get(
        self,
        key,
    ):
        with self._lock:

            entry = self._cache.get(key)

            if entry is None:
                return None

            if (
                datetime.now()
                >= entry.expires_at
            ):
                del self._cache[key]
                return None

            return entry.value

    def put(
        self,
        key,
        value,
    ):
        with self._lock:

            self._cache[key] = CacheEntry(
                value=value,
                expires_at=(
                    datetime.now()
                    + self.ttl
                ),
            )

    def invalidate(
        self,
        key=None,
    ):
        with self._lock:

            if key is None:
                self._cache.clear()
                return

            self._cache.pop(
                key,
                None,
            )

    def statistics(self):
        with self._lock:

            return {
                "count": len(
                    self._cache
                ),
                "ttl_seconds": int(
                    self.ttl.total_seconds()
                ),
            }