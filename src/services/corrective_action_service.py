from __future__ import annotations

from datetime import datetime

from src.framework.exception import NotFoundError, ValidationError
from src.models.corrective_action import CorrectiveAction
from src.models.production_ng import ProductionNG
from src.repository.corrective_action_repository import (
    CorrectiveActionRepository,
)
from src.services.base_service import SessionOwnedService


class CorrectiveActionService(SessionOwnedService):
    """
    Giai đoạn 6 (Quality, 2026-07-25): quản lý hành động khắc phục /
    phòng ngừa (CAPA) gắn với một bản ghi NG (`ProductionNG`).

    Giống Giai đoạn 4 (Tool/SparePart/StockIn/StockOut), đây là service
    MỚI có nhu cầu hiển thị dữ liệu vừa tạo ngay lập tức từ một
    session/page khác (ví dụ: tạo CAPA từ CorrectiveActionPage, rồi
    NGAnalysisPage cần thấy ngay CAPA đó) - nên gọi `self.commit()`
    (không phải chỉ flush) sau mỗi create/update, đúng theo bài học từ
    Giai đoạn 4 (bug cross-service commit visibility).
    """

    ACTION_TYPE_CORRECTIVE = "CORRECTIVE"
    ACTION_TYPE_PREVENTIVE = "PREVENTIVE"

    VALID_ACTION_TYPES = {
        ACTION_TYPE_CORRECTIVE,
        ACTION_TYPE_PREVENTIVE,
    }

    STATUS_OPEN = "OPEN"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_DONE = "DONE"
    STATUS_VERIFIED = "VERIFIED"
    STATUS_CANCELLED = "CANCELLED"

    VALID_STATUSES = {
        STATUS_OPEN,
        STATUS_IN_PROGRESS,
        STATUS_DONE,
        STATUS_VERIFIED,
        STATUS_CANCELLED,
    }

    def __init__(
        self,
        session=None,
    ):
        super().__init__(session=session)

        self.repository = CorrectiveActionRepository(
            self.session
        )

    # ==========================================================
    # Query
    # ==========================================================

    def get_all(self):
        return self.repository.get_all_ordered()

    def get_by_id(
        self,
        action_id,
    ):
        return self.repository.get_by_id(action_id)

    def get_by_ng_id(
        self,
        ng_id,
    ):
        return self.repository.get_by_ng_id(ng_id)

    def get_open_actions(self):
        return self.repository.get_open_actions()

    # ==========================================================
    # Create
    # ==========================================================

    def create_action(
        self,
        data,
    ):
        ng_id = self._normalize_ng_id(
            data.get("ng_id")
        )

        self._require_ng(ng_id)

        action = CorrectiveAction(
            ng_id=ng_id,
            action_type=self._normalize_action_type(
                data.get("action_type")
            ),
            description=self._require_text(
                data.get("description"),
                "Description",
            ),
            assigned_to=self._clean_optional_upper(
                data.get("assigned_to")
            ),
            due_date=self._normalize_datetime(
                data.get("due_date")
            ),
            status=self.STATUS_OPEN,
            remark=self._clean_optional_text(
                data.get("remark")
            ),
        )

        self.repository.add(action)

        self.commit()

        return action

    # ==========================================================
    # Update
    # ==========================================================

    def update_action(
        self,
        action_id,
        data,
    ):
        action = self._require_action(action_id)

        action.action_type = self._normalize_action_type(
            data.get(
                "action_type",
                action.action_type,
            )
        )

        action.description = self._require_text(
            data.get(
                "description",
                action.description,
            ),
            "Description",
        )

        if "assigned_to" in data:
            action.assigned_to = (
                self._clean_optional_upper(
                    data.get("assigned_to")
                )
            )

        if "due_date" in data:
            action.due_date = (
                self._normalize_datetime(
                    data.get("due_date")
                )
            )

        if "remark" in data:
            action.remark = (
                self._clean_optional_text(
                    data.get("remark")
                )
            )

        self.repository.update()

        self.commit()

        return action

    def update_status(
        self,
        action_id,
        status,
        *,
        verified_by=None,
        effectiveness_note=None,
    ):
        action = self._require_action(action_id)

        normalized_status = self._normalize_status(
            status
        )

        action.status = normalized_status

        if normalized_status == self.STATUS_DONE:
            action.completed_at = datetime.now()

        if normalized_status == self.STATUS_VERIFIED:
            if action.completed_at is None:
                action.completed_at = datetime.now()

            action.verified_at = datetime.now()
            action.verified_by = (
                self._clean_optional_upper(
                    verified_by
                )
            )
            action.effectiveness_note = (
                self._clean_optional_text(
                    effectiveness_note
                )
            )

        self.repository.update()

        self.commit()

        return action

    # ==========================================================
    # Validation
    # ==========================================================

    def _require_action(
        self,
        action_id,
    ):
        action = self.get_by_id(action_id)

        if action is None:
            raise NotFoundError(
                f"Corrective Action not found: {action_id}"
            )

        return action

    def _require_ng(
        self,
        ng_id,
    ):
        record = (
            self.session
            .query(ProductionNG)
            .filter(ProductionNG.id == ng_id)
            .first()
        )

        if record is None:
            raise NotFoundError(
                f"Production NG not found: {ng_id}"
            )

        return record

    @staticmethod
    def _normalize_ng_id(
        value,
    ):
        try:
            return int(value)
        except (TypeError, ValueError) as error:
            raise ValidationError(
                f"Invalid NG ID: {value}"
            ) from error

    @classmethod
    def _normalize_action_type(
        cls,
        value,
    ):
        normalized = str(
            value or ""
        ).strip().upper()

        if normalized not in cls.VALID_ACTION_TYPES:
            raise ValidationError(
                f"Invalid Action Type: {normalized}"
            )

        return normalized

    @classmethod
    def _normalize_status(
        cls,
        value,
    ):
        normalized = str(
            value or ""
        ).strip().upper()

        if normalized not in cls.VALID_STATUSES:
            raise ValidationError(
                f"Invalid Status: {normalized}"
            )

        return normalized

    @staticmethod
    def _require_text(
        value,
        field_name,
    ):
        text = str(value or "").strip()

        if not text:
            raise ValidationError(
                f"{field_name} is required."
            )

        return text

    @staticmethod
    def _normalize_datetime(
        value,
    ):
        if value is None or value == "":
            return None

        if isinstance(value, datetime):
            return value

        text = str(value).strip()

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d/%m/%Y",
        ]

        for date_format in formats:
            try:
                return datetime.strptime(
                    text,
                    date_format,
                )
            except ValueError:
                continue

        try:
            return datetime.fromisoformat(text)
        except ValueError as error:
            raise ValidationError(
                f"Invalid datetime value: {value}"
            ) from error

    @staticmethod
    def _clean_optional_upper(
        value,
    ):
        text = str(value or "").strip().upper()

        return text or None

    @staticmethod
    def _clean_optional_text(
        value,
    ):
        text = str(value or "").strip()

        return text or None
