from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox


class LookupComboBox(QComboBox):
    """
    ComboBox dùng cho dữ liệu tra cứu Master.

    Mỗi item gồm:

        text hiển thị
        key nghiệp vụ
        object model tùy chọn

    Ví dụ:

        P001 - Sản phẩm A
        key = P001
        object = Product instance
    """

    value_changed = Signal(str)

    ROLE_KEY = Qt.UserRole
    ROLE_OBJECT = Qt.UserRole + 1

    def __init__(
        self,
        parent=None,
        placeholder="-- Select --",
    ):
        super().__init__(parent)

        self.placeholder = placeholder

        self.setEditable(False)
        self.setMinimumWidth(220)

        self.currentIndexChanged.connect(
            self._emit_value_changed
        )

        self.clear_items()

    # ==========================================================
    # Data
    # ==========================================================

    def clear_items(self):
        """
        Xóa dữ liệu và thêm placeholder.
        """
        self.blockSignals(True)

        self.clear()
        self.addItem(self.placeholder)

        self.setItemData(
            0,
            "",
            self.ROLE_KEY,
        )

        self.setItemData(
            0,
            None,
            self.ROLE_OBJECT,
        )

        self.setCurrentIndex(0)

        self.blockSignals(False)

    def set_items(
        self,
        items,
        key_getter,
        text_getter,
    ):
        """
        Nạp danh sách object vào ComboBox.

        Args:
            items:
                Danh sách model hoặc dictionary.

            key_getter:
                callable(item) -> key

            text_getter:
                callable(item) -> text hiển thị
        """
        if not callable(key_getter):
            raise ValueError(
                "key_getter must be callable."
            )

        if not callable(text_getter):
            raise ValueError(
                "text_getter must be callable."
            )

        current_value = self.current_value()

        self.clear_items()

        for item in items or []:
            key = str(
                key_getter(item) or ""
            ).strip().upper()

            if not key:
                continue

            text = str(
                text_getter(item) or key
            ).strip()

            self.addItem(text)

            index = self.count() - 1

            self.setItemData(
                index,
                key,
                self.ROLE_KEY,
            )

            self.setItemData(
                index,
                item,
                self.ROLE_OBJECT,
            )

        if current_value:
            self.set_current_value(
                current_value
            )

    def add_lookup_item(
        self,
        key,
        text,
        obj=None,
    ):
        key = str(
            key or ""
        ).strip().upper()

        if not key:
            return

        self.addItem(
            str(text or key)
        )

        index = self.count() - 1

        self.setItemData(
            index,
            key,
            self.ROLE_KEY,
        )

        self.setItemData(
            index,
            obj,
            self.ROLE_OBJECT,
        )

    # ==========================================================
    # Selection
    # ==========================================================

    def current_value(self):
        value = self.currentData(
            self.ROLE_KEY
        )

        return str(
            value or ""
        ).strip().upper()

    def current_object(self):
        return self.currentData(
            self.ROLE_OBJECT
        )

    def set_current_value(self, value):
        value = str(
            value or ""
        ).strip().upper()

        if not value:
            self.setCurrentIndex(0)
            return False

        for index in range(
            1,
            self.count(),
        ):
            item_value = str(
                self.itemData(
                    index,
                    self.ROLE_KEY,
                )
                or ""
            ).strip().upper()

            if item_value == value:
                self.setCurrentIndex(index)
                return True

        self.setCurrentIndex(0)
        return False

    def has_value(self, value):
        value = str(
            value or ""
        ).strip().upper()

        for index in range(
            1,
            self.count(),
        ):
            if (
                str(
                    self.itemData(
                        index,
                        self.ROLE_KEY,
                    )
                    or ""
                )
                .strip()
                .upper()
                == value
            ):
                return True

        return False

    # ==========================================================
    # Validation
    # ==========================================================

    def require_value(
        self,
        field_name="Selection",
    ):
        value = self.current_value()

        if not value:
            raise ValueError(
                f"{field_name} is required."
            )

        return value

    # ==========================================================
    # Events
    # ==========================================================

    def _emit_value_changed(self, _index):
        self.value_changed.emit(
            self.current_value()
        )