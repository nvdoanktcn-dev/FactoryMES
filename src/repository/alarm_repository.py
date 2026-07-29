from __future__ import annotations

from src.models.alarm import Alarm
from src.repository.base_repository import BaseRepository


class AlarmRepository(BaseRepository):
    def __init__(
        self,
        session,
    ):
        super().__init__(
            session=session,
            model=Alarm,
        )

    def get_by_id(
        self,
        alarm_id,
    ):
        try:
            normalized_id = int(alarm_id)
        except (TypeError, ValueError):
            return None

        return (
            self.session
            .query(Alarm)
            .filter(
                Alarm.id == normalized_id
            )
            .first()
        )

    def get_all_ordered(
        self,
        limit=None,
    ):
        query = (
            self.session
            .query(Alarm)
            .order_by(
                Alarm.raised_at.desc(),
                Alarm.id.desc(),
            )
        )

        if limit:
            query = query.limit(int(limit))

        return query.all()

    def get_open_alarms(
        self,
        limit=None,
    ):
        query = (
            self.session
            .query(Alarm)
            .filter(
                Alarm.status.in_(
                    ["OPEN", "ACKNOWLEDGED"]
                )
            )
            .order_by(
                Alarm.raised_at.desc(),
                Alarm.id.desc(),
            )
        )

        if limit:
            query = query.limit(int(limit))

        return query.all()

    def get_by_machine_id(
        self,
        machine_id,
    ):
        return (
            self.session
            .query(Alarm)
            .filter(
                Alarm.machine_id == int(machine_id)
            )
            .order_by(
                Alarm.raised_at.desc(),
                Alarm.id.desc(),
            )
            .all()
        )

    def count_open_by_machine_id(
        self,
        machine_id,
    ):
        return (
            self.session
            .query(Alarm)
            .filter(
                Alarm.machine_id == int(machine_id),
                Alarm.status.in_(
                    ["OPEN", "ACKNOWLEDGED"]
                ),
            )
            .count()
        )

    def count_open_by_machine_map(self):
        """
        Trả về dict {machine_id: số alarm đang mở} cho TẤT CẢ máy có
        alarm đang mở - dùng cho Live Dashboard (1 query thay vì N).
        """
        rows = (
            self.session
            .query(Alarm)
            .filter(
                Alarm.status.in_(
                    ["OPEN", "ACKNOWLEDGED"]
                )
            )
            .all()
        )

        counts = {}
        for row in rows:
            counts[row.machine_id] = (
                counts.get(row.machine_id, 0) + 1
            )

        return counts
