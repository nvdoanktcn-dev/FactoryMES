from __future__ import annotations

from src.framework.exception import ValidationError

# Giai đoạn 4 (Warehouse nâng cao, 2026-07-25): liên kết Xuất/Nhập/Tồn
# thực sự - StockIn/StockOut giờ khai báo item_type để đối chiếu
# item_code với đúng danh mục (Product/Tool/SparePart) thay vì chỉ là
# text tự do. OTHER giữ nguyên hành vi cũ (không đối chiếu danh mục nào)
# để tương thích ngược với dữ liệu và Import Excel đã có từ trước.

ITEM_TYPE_OTHER = "OTHER"
ITEM_TYPE_PRODUCT = "PRODUCT"
ITEM_TYPE_TOOL = "TOOL"
ITEM_TYPE_SPARE_PART = "SPARE_PART"

VALID_ITEM_TYPES = {
    ITEM_TYPE_OTHER,
    ITEM_TYPE_PRODUCT,
    ITEM_TYPE_TOOL,
    ITEM_TYPE_SPARE_PART,
}

# Nhãn hiển thị cho UI (combo box item_type trên StockIn/StockOut Dialog).
ITEM_TYPE_LABELS = {
    ITEM_TYPE_OTHER: "Other",
    ITEM_TYPE_PRODUCT: "Product",
    ITEM_TYPE_TOOL: "Tool",
    ITEM_TYPE_SPARE_PART: "Spare Part",
}


def normalize_item_type(value):
    text = str(value or ITEM_TYPE_OTHER).strip().upper()

    if text not in VALID_ITEM_TYPES:
        raise ValidationError(f"Invalid Item Type: {text}")

    return text


def validate_item_reference(session, item_type, item_code):
    """
    Đối chiếu item_code với đúng danh mục dựa trên item_type.

    - OTHER: không đối chiếu (tương thích ngược).
    - PRODUCT/TOOL/SPARE_PART: item_code phải tồn tại trong danh mục
      tương ứng, nếu không sẽ raise ValidationError.

    session được TRUYỀN VÀO (mượn), không sở hữu - catalog_service tạo
    ở đây sẽ không bao giờ commit/close session này (xem
    BaseService._owns_session).
    """

    if item_type == ITEM_TYPE_OTHER:
        return

    if item_type == ITEM_TYPE_PRODUCT:
        from src.services.product_service import ProductService

        catalog_service = ProductService(session=session)
        label = "Product"

    elif item_type == ITEM_TYPE_TOOL:
        from src.services.tool_service import ToolService

        catalog_service = ToolService(session=session)
        label = "Tool"

    elif item_type == ITEM_TYPE_SPARE_PART:
        from src.services.spare_part_service import SparePartService

        catalog_service = SparePartService(session=session)
        label = "Spare Part"

    else:
        # Không thể xảy ra nếu normalize_item_type() đã được gọi trước,
        # nhưng vẫn phòng hờ.
        raise ValidationError(f"Invalid Item Type: {item_type}")

    record = catalog_service.get_by_code(item_code)

    if record is None:
        raise ValidationError(
            f"{label} not found in catalog: {item_code}"
        )
