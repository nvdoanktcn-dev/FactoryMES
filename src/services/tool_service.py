from __future__ import annotations

from sqlalchemy.orm import Session

from src.framework.exception import DuplicateError, NotFoundError
from src.framework.validator import BaseValidator
from src.models.tool import Tool
from src.repository.tool_repository import ToolRepository
from src.services.base_service import SessionOwnedService


class ToolService(SessionOwnedService):
    """
    Service quản lý danh mục Dụng cụ (Tool Warehouse) — Giai đoạn 4.
    """

    STATUS_ACTIVE = "ACTIVE"
    STATUS_MAINTENANCE = "MAINTENANCE"
    STATUS_STOPPED = "STOPPED"

    VALID_STATUS = {
        STATUS_ACTIVE,
        STATUS_MAINTENANCE,
        STATUS_STOPPED,
    }

    def __init__(
        self,
        session: Session | None = None,
        repository: ToolRepository | None = None,
    ) -> None:
        if repository is not None:
            super().__init__(
                session=getattr(repository, "session", None)
            )
            self._owns_session = False
            self.repository = repository
            return

        super().__init__(session=session)

        self.repository = ToolRepository(
            self.require_session()
        )

    # ==========================================================
    # Query
    # ==========================================================

    def get_all_tools(self):
        return self.repository.get_all()

    def get_tool(self, tool_code):
        code = self._normalize_code(tool_code)

        if not code:
            return None

        return self.repository.get_by_code(code)

    def get_by_code(self, tool_code):
        return self.get_tool(tool_code)

    def search_tools(self, keyword):
        tools = self.get_all_tools()

        text = str(keyword or "").strip().lower()

        if not text:
            return tools

        return [
            tool
            for tool in tools
            if (
                text in str(tool.tool_code or "").lower()
                or text in str(tool.tool_name or "").lower()
                or text in str(tool.tool_type or "").lower()
                or text in str(tool.location or "").lower()
                or text in str(tool.status or "").lower()
            )
        ]

    # ==========================================================
    # Create
    # ==========================================================

    def create_tool(self, data):
        normalized = self._normalize_data(data)

        tool_code = normalized["tool_code"]
        tool_name = normalized["tool_name"]

        self._validate_tool(
            tool_code=tool_code,
            tool_name=tool_name,
        )

        if self.repository.exists(tool_code):
            raise DuplicateError(
                f"Tool already exists: {tool_code}"
            )

        tool = Tool(**normalized)

        self.log_info(f"Create Tool: {tool_code}")

        created = self.repository.add(tool)

        # Giai đoạn 4 (Warehouse nâng cao, 2026-07-25): commit ngay sau
        # khi tạo, KHÔNG chờ tới khi service.close(). ToolService là
        # danh mục được đối chiếu trực tiếp (FK sống) bởi StockIn/
        # StockOut ở một Service/Session KHÁC (mỗi trang có session
        # riêng - xem get_session()). Nếu không commit ngay, Tool vừa
        # tạo ở tab "Tool Warehouse" sẽ KHÔNG thấy được từ tab "Stock
        # In" cho tới khi đóng app - lỗi "Tool not found in catalog"
        # dù người dùng vừa mới tạo Tool đó trong cùng phiên làm việc.
        self.commit()

        return created

    # ==========================================================
    # Update
    # ==========================================================

    def update_tool(self, tool_code, data):
        code = self._normalize_code(tool_code)

        tool = self.repository.get_by_code(code)

        if tool is None:
            raise NotFoundError(f"Tool not found: {code}")

        normalized = self._normalize_data(
            {**dict(data or {}), "tool_code": code}
        )

        self._validate_tool(
            tool_code=code,
            tool_name=normalized["tool_name"],
        )

        tool.tool_name = normalized["tool_name"]
        tool.tool_type = normalized["tool_type"]
        tool.location = normalized["location"]
        tool.unit = normalized["unit"]
        tool.min_stock = normalized["min_stock"]
        tool.status = normalized["status"]
        tool.remark = normalized["remark"]

        self.log_info(f"Update Tool: {code}")

        self.repository.update()

        # Xem giải thích ở create_tool() - commit ngay để các Service/
        # Session khác (StockIn/StockOut, Inventory Balance) thấy được
        # thay đổi (VD: min_stock mới) ngay trong cùng phiên làm việc.
        self.commit()

        return tool

    # ==========================================================
    # Deactivate
    # ==========================================================

    def delete_tool(self, tool_code):
        code = self._normalize_code(tool_code)

        tool = self.repository.get_by_code(code)

        if tool is None:
            raise NotFoundError(f"Tool not found: {code}")

        tool.status = self.STATUS_STOPPED

        self.log_warning(f"Stopped Tool: {code}")

        self.repository.update()

        self.commit()

        return tool

    # ==========================================================
    # Validation and normalization
    # ==========================================================

    @staticmethod
    def _validate_tool(tool_code, tool_name):
        BaseValidator.required(tool_code, "Tool Code")
        BaseValidator.required(tool_name, "Tool Name")
        BaseValidator.max_length(tool_code, "Tool Code", 30)
        BaseValidator.max_length(tool_name, "Tool Name", 100)

    @classmethod
    def _normalize_data(cls, data):
        data = dict(data or {})

        return {
            "tool_code": cls._normalize_code(
                data.get("tool_code")
            ),
            "tool_name": cls._clean_text(
                data.get("tool_name")
            ),
            "tool_type": cls._clean_optional_text(
                data.get("tool_type")
            ),
            "location": cls._clean_optional_text(
                data.get("location")
            ),
            "unit": cls._clean_optional_text(
                data.get("unit")
            ),
            "min_stock": cls._parse_float(
                data.get("min_stock")
            ),
            "status": cls._normalize_status(
                data.get("status")
            ),
            "remark": cls._clean_optional_text(
                data.get("remark")
            ),
        }

    @staticmethod
    def _normalize_code(value):
        return str(value or "").strip().upper()

    @staticmethod
    def _clean_text(value):
        return str(value or "").strip()

    @staticmethod
    def _clean_optional_text(value):
        text = str(value or "").strip()
        return text or None

    @staticmethod
    def _parse_float(value):
        if value in (None, ""):
            return 0.0

        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def _normalize_status(cls, value):
        status = str(value or cls.STATUS_ACTIVE).strip().upper()

        if status not in cls.VALID_STATUS:
            raise ValueError(f"Invalid Tool Status: {status}")

        return status
