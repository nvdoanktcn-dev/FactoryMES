"""
Compatibility wrapper for Master Import Center.

NavigationManager cũ import MasterImportPage từ:
    src.ui.pages.master_import_page

Implementation mới nằm tại:
    src.ui.master_import.master_import_page
"""

from src.ui.master_import.master_import_page import (
    MasterImportPage,
)

__all__ = [
    "MasterImportPage",
]