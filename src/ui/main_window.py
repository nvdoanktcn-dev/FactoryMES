from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui.navigation.menu_manager import MenuManager
from src.ui.navigation.navigation_manager import (
    NavigationManager,
)
from src.ui.theme.theme_manager import ThemeManager


class MainWindow(QMainWindow):
    """
    Cửa sổ chính của FactoryMES.

    Chức năng chính:

    - Hiển thị menu điều hướng bên trái.
    - Lazy-load page khi người dùng mở lần đầu.
    - Hiển thị page trong QStackedWidget.
    - Quản lý theme.
    - Đóng controller/service/session khi thoát ứng dụng.
    """

    DEFAULT_PAGE = "Dashboard"

    def __init__(
        self,
        parent=None,
        dashboard_controller=None,
    ) -> None:
        super().__init__(parent)

        self.dashboard_controller = (
            dashboard_controller
        )

        self.setObjectName(
            "FactoryMESMainWindow"
        )

        self.setWindowTitle(
            "FactoryMES V1.0"
        )

        self.resize(
            1600,
            950,
        )

        self.setMinimumSize(
            1200,
            720,
        )

        self.navigation = QTreeWidget(
            self
        )

        self.stack = QStackedWidget(
            self
        )

        self.title_label = QLabel(
            self
        )

        self.footer_label = QLabel(
            self
        )

        self.btn_theme = QPushButton(
            "🌙 Theme",
            self,
        )

        self.navigation_manager = (
            NavigationManager(
                self.stack,
                dashboard_controller=(
                    self.dashboard_controller
                ),
            )
        )

        self._is_closing = False

        self.build_ui()
        self.build_navigation()
        self.connect_events()
        self.open_default_page()

    # ==========================================================
    # UI
    # ==========================================================

    def build_ui(
        self,
    ) -> None:
        central_widget = QWidget(
            self
        )

        central_widget.setObjectName(
            "FactoryMESCentralWidget"
        )

        root_layout = QVBoxLayout(
            central_widget
        )

        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root_layout.setSpacing(
            0
        )

        root_layout.addWidget(
            self.create_header()
        )

        root_layout.addWidget(
            self.create_body(),
            1,
        )

        root_layout.addWidget(
            self.create_footer()
        )

        self.setCentralWidget(
            central_widget
        )

        self.apply_style()

    def create_header(
        self,
    ) -> QWidget:
        header = QWidget(
            self
        )

        header.setObjectName(
            "FactoryMESHeader"
        )

        layout = QHBoxLayout(
            header
        )

        layout.setContentsMargins(
            16,
            8,
            16,
            8,
        )

        layout.setSpacing(
            10
        )

        self.update_title()

        self.title_label.setObjectName(
            "FactoryMESTitle"
        )

        self.title_label.setAlignment(
            Qt.AlignLeft
            | Qt.AlignVCenter
        )

        self.btn_theme.setObjectName(
            "FactoryMESThemeButton"
        )

        self.btn_theme.setMinimumWidth(
            110
        )

        layout.addWidget(
            self.title_label,
            1,
        )

        layout.addWidget(
            self.btn_theme
        )

        return header

    def create_body(
        self,
    ) -> QWidget:
        body = QWidget(
            self
        )

        body.setObjectName(
            "FactoryMESBody"
        )

        layout = QHBoxLayout(
            body
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            0
        )

        self.configure_navigation()
        self.configure_stack()

        layout.addWidget(
            self.navigation
        )

        layout.addWidget(
            self.stack,
            1,
        )

        return body

    def create_footer(
        self,
    ) -> QWidget:
        footer = QWidget(
            self
        )

        footer.setObjectName(
            "FactoryMESFooter"
        )

        layout = QHBoxLayout(
            footer
        )

        layout.setContentsMargins(
            12,
            5,
            12,
            5,
        )

        self.footer_label.setObjectName(
            "FactoryMESFooterLabel"
        )

        self.footer_label.setText(
            "FactoryMES Framework V1.0"
            "  |  Database Connected"
        )

        layout.addWidget(
            self.footer_label
        )

        layout.addStretch()

        return footer

    def configure_navigation(
        self,
    ) -> None:
        self.navigation.setObjectName(
            "FactoryMESNavigation"
        )

        self.navigation.setHeaderHidden(
            True
        )

        self.navigation.setMinimumWidth(
            230
        )

        self.navigation.setMaximumWidth(
            310
        )

        self.navigation.setIndentation(
            16
        )

        self.navigation.setAnimated(
            True
        )

        self.navigation.setExpandsOnDoubleClick(
            True
        )

        self.navigation.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Expanding,
        )

    def configure_stack(
        self,
    ) -> None:
        self.stack.setObjectName(
            "FactoryMESContentStack"
        )

        self.stack.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

    # ==========================================================
    # Navigation setup
    # ==========================================================

    def build_navigation(
        self,
    ) -> None:
        """
        Tạo menu và đăng ký page factories.

        Không tạo toàn bộ QWidget ở bước này.
        """

        self.navigation.clear()

        MenuManager.build_menu(
            self.navigation
        )

        self.navigation_manager.build_pages()

        self.navigation.expandAll()

    def connect_events(
        self,
    ) -> None:
        self.navigation.itemClicked.connect(
            self.on_menu_clicked
        )

        self.btn_theme.clicked.connect(
            self.toggle_theme
        )

    # ==========================================================
    # Navigation events
    # ==========================================================

    def on_menu_clicked(
        self,
        item,
        column=0,
    ) -> None:
        del column

        if item is None:
            return

        page_name = item.data(
            0,
            Qt.UserRole,
        )

        if page_name is None:
            item.setExpanded(
                not item.isExpanded()
            )
            return

        page_name = str(
            page_name
        ).strip()

        if not page_name:
            return

        if not self.navigation_manager.has_page(
            page_name
        ):
            self.set_footer_status(
                (
                    "Navigation Error: "
                    f"Page '{page_name}' "
                    "is not registered."
                )
            )
            return

        try:
            self.navigation_manager.navigate(
                page_name
            )

            self.set_footer_status(
                f"Current Page: {page_name}"
            )

        except Exception as error:
            self.set_footer_status(
                f"Navigation Error: {error}"
            )

    def open_default_page(
        self,
    ) -> None:
        """
        Mở page mặc định.

        Dashboard chỉ được tạo tại đây, sau khi menu và factory
        đã được đăng ký.
        """

        if not self.navigation_manager.has_page(
            self.DEFAULT_PAGE
        ):
            self.open_first_available_page()
            return

        try:
            self.navigation_manager.navigate(
                self.DEFAULT_PAGE
            )

            self.select_navigation_item(
                self.DEFAULT_PAGE
            )

            self.set_footer_status(
                (
                    "Current Page: "
                    f"{self.DEFAULT_PAGE}"
                )
            )

        except Exception as error:
            self.set_footer_status(
                f"Dashboard Error: {error}"
            )

            self.open_first_available_page(
                excluded_page=(
                    self.DEFAULT_PAGE
                )
            )

    def open_first_available_page(
        self,
        excluded_page=None,
    ) -> None:
        """
        Mở page đầu tiên có thể tạo được.

        Dùng khi Dashboard không tồn tại hoặc tạo thất bại.
        """

        page_names = (
            self.navigation_manager
            .page_names()
        )

        if not page_names:
            self.set_footer_status(
                "No application page is registered."
            )
            return

        normalized_excluded = str(
            excluded_page or ""
        ).strip()

        for page_name in page_names:
            if (
                normalized_excluded
                and page_name
                == normalized_excluded
            ):
                continue

            try:
                self.navigation_manager.navigate(
                    page_name
                )

                self.select_navigation_item(
                    page_name
                )

                self.set_footer_status(
                    (
                        "Current Page: "
                        f"{page_name}"
                    )
                )

                return

            except Exception:
                continue

        self.set_footer_status(
            "No application page could be opened."
        )

    def navigate_to(
        self,
        page_name: str,
    ) -> bool:
        """
        Điều hướng bằng code từ module khác.

        Trả về True nếu thành công.
        """

        page_name = str(
            page_name or ""
        ).strip()

        if not page_name:
            return False

        if not self.navigation_manager.has_page(
            page_name
        ):
            self.set_footer_status(
                (
                    "Navigation Error: "
                    f"Page '{page_name}' "
                    "is not registered."
                )
            )
            return False

        try:
            self.navigation_manager.navigate(
                page_name
            )

            self.select_navigation_item(
                page_name
            )

            self.set_footer_status(
                f"Current Page: {page_name}"
            )

            return True

        except Exception as error:
            self.set_footer_status(
                f"Navigation Error: {error}"
            )

            return False

    # ==========================================================
    # Navigation tree helpers
    # ==========================================================

    def select_navigation_item(
        self,
        page_name,
    ) -> None:
        root_item = (
            self.navigation
            .invisibleRootItem()
        )

        item = self.find_tree_item_by_key(
            root_item,
            page_name,
        )

        if item is not None:
            self.navigation.setCurrentItem(
                item
            )

    @classmethod
    def find_tree_item_by_key(
        cls,
        parent_item,
        page_key,
    ):
        normalized_key = str(
            page_key or ""
        ).strip()

        if not normalized_key:
            return None

        for index in range(
            parent_item.childCount()
        ):
            child = parent_item.child(
                index
            )

            child_key = child.data(
                0,
                Qt.UserRole,
            )

            if (
                child_key is not None
                and str(child_key).strip()
                == normalized_key
            ):
                return child

            nested_item = (
                cls.find_tree_item_by_key(
                    child,
                    normalized_key,
                )
            )

            if nested_item is not None:
                return nested_item

        return None

    @classmethod
    def find_tree_item(
        cls,
        parent_item,
        text,
    ):
        """
        Giữ tương thích với code cũ.

        Menu hiện tại sử dụng khóa trong Qt.UserRole.
        """

        return cls.find_tree_item_by_key(
            parent_item,
            text,
        )

    # ==========================================================
    # Current page helpers
    # ==========================================================

    def current_page_name(
        self,
    ):
        return (
            self.navigation_manager
            .current_page_name()
        )

    def current_page(
        self,
    ):
        page_name = self.current_page_name()

        if page_name is None:
            return None

        return (
            self.navigation_manager
            .get_page(page_name)
        )

    def reload_current_page(
        self,
    ) -> bool:
        page_name = self.current_page_name()

        if page_name is None:
            return False

        try:
            self.navigation_manager.reload_page(
                page_name
            )

            self.set_footer_status(
                (
                    "Reloaded Page: "
                    f"{page_name}"
                )
            )

            return True

        except Exception as error:
            self.set_footer_status(
                f"Reload Error: {error}"
            )

            return False

    # ==========================================================
    # Theme
    # ==========================================================

    def toggle_theme(
        self,
    ) -> None:
        app = QApplication.instance()

        if app is None:
            return

        try:
            ThemeManager.toggle_theme(
                app
            )

        except Exception as error:
            self.set_footer_status(
                f"Theme Error: {error}"
            )

    # ==========================================================
    # Header / Footer
    # ==========================================================

    def update_title(
        self,
    ) -> None:
        current_time = (
            datetime.now()
            .strftime(
                "%Y-%m-%d %H:%M"
            )
        )

        self.title_label.setText(
            "🏭 FactoryMES V1.0"
            f"  |  {current_time}"
        )

    def set_footer_status(
        self,
        message,
    ) -> None:
        self.footer_label.setText(
            "FactoryMES Framework V1.0"
            f"  |  {str(message or '')}"
        )

    # ==========================================================
    # Lifecycle
    # ==========================================================

    def closeEvent(
        self,
        event,
    ) -> None:
        """
        Đóng toàn bộ page đã được tạo.

        Các page chưa từng được mở không tồn tại nên không cần đóng.
        """

        if self._is_closing:
            event.accept()
            return

        self._is_closing = True

        try:
            self.navigation_manager.close_all_pages()

        except Exception as error:
            self.set_footer_status(
                f"Shutdown Warning: {error}"
            )

        finally:
            super().closeEvent(
                event
            )

    # ==========================================================
    # Style
    # ==========================================================

    def apply_style(
        self,
    ) -> None:
        self.setStyleSheet(
            """
            QWidget#FactoryMESCentralWidget {
                background: #F4F6F8;
            }

            QWidget#FactoryMESHeader {
                background: #1976D2;
            }

            QLabel#FactoryMESTitle {
                color: white;
                font-size: 18px;
                font-weight: bold;
            }

            QPushButton#FactoryMESThemeButton {
                min-height: 31px;
                padding: 3px 12px;
                background: white;
                color: #263238;
                border: 1px solid #CFD8DC;
                border-radius: 5px;
                font-weight: bold;
            }

            QPushButton#FactoryMESThemeButton:hover {
                background: #ECEFF1;
            }

            QTreeWidget#FactoryMESNavigation {
                background: #263238;
                color: white;
                font-size: 14px;
                border: none;
                outline: none;
            }

            QTreeWidget#FactoryMESNavigation::item {
                min-height: 34px;
                padding: 4px 8px;
                border: none;
            }

            QTreeWidget#FactoryMESNavigation::item:hover {
                background: #37474F;
            }

            QTreeWidget#FactoryMESNavigation::item:selected {
                background: #1976D2;
                color: white;
            }

            QStackedWidget#FactoryMESContentStack {
                background: #F4F6F8;
                border: none;
            }

            QWidget#FactoryMESFooter {
                background: #ECEFF1;
                border-top: 1px solid #CFD8DC;
            }

            QLabel#FactoryMESFooterLabel {
                color: #37474F;
                font-size: 11px;
            }
            """
        )