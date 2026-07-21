class WorkOrderSchema:
    """
    Schema chuẩn cho Work Order Master Import.

    Chịu trách nhiệm:
    - Mapping tên cột Excel
    - Chuẩn hóa Status/Priority
    - Kiểm tra dữ liệu cơ bản

    Không truy cập database.
    """

    REQUIRED_COLUMNS = [
        "Work Order No",
        "Product Code",
        "Plan Qty",
    ]

    OPTIONAL_COLUMNS = [
        "Completed Qty",
        "NG Qty",
        "Start Date",
        "Due Date",
        "Finish Date",
        "Status",
        "Priority",
        "Remark",
    ]

    COLUMN_MAPPING = {
        # Work Order
        "Work Order No": "Work Order No",
        "Work Order": "Work Order No",
        "WO": "Work Order No",
        "Mã công lệnh": "Work Order No",
        "Mã lệnh sản xuất": "Work Order No",
        "生产工单": "Work Order No",
        "工单号": "Work Order No",

        # Product
        "Product Code": "Product Code",
        "Mã sản phẩm": "Product Code",
        "Mã hàng": "Product Code",
        "产品编码": "Product Code",
        "产品代码": "Product Code",

        # Quantities
        "Plan Qty": "Plan Qty",
        "Planned Qty": "Plan Qty",
        "Số lượng kế hoạch": "Plan Qty",
        "Số lượng công lệnh": "Plan Qty",
        "计划数量": "Plan Qty",

        "Completed Qty": "Completed Qty",
        "Số lượng hoàn thành": "Completed Qty",
        "Sản lượng hoàn thành": "Completed Qty",
        "完成数量": "Completed Qty",

        "NG Qty": "NG Qty",
        "Số lượng NG": "NG Qty",
        "Tổng NG": "NG Qty",
        "不良数量": "NG Qty",

        # Dates
        "Start Date": "Start Date",
        "Ngày bắt đầu": "Start Date",
        "Ngày sản xuất": "Start Date",
        "开始日期": "Start Date",

        "Due Date": "Due Date",
        "Ngày đến hạn": "Due Date",
        "Ngày giao hàng": "Due Date",
        "截止日期": "Due Date",
        "交期": "Due Date",

        "Finish Date": "Finish Date",
        "Ngày hoàn thành": "Finish Date",
        "完成日期": "Finish Date",

        # Status
        "Status": "Status",
        "Trạng thái": "Status",
        "状态": "Status",

        # Priority
        "Priority": "Priority",
        "Mức ưu tiên": "Priority",
        "Độ ưu tiên": "Priority",
        "优先级": "Priority",

        # Remark
        "Remark": "Remark",
        "Ghi chú": "Remark",
        "备注": "Remark",
    }

    VALID_STATUSES = {
        "PLANNED",
        "RELEASED",
        "RUNNING",
        "PAUSED",
        "COMPLETED",
        "CLOSED",
    }

    STATUS_MAPPING = {
        "PLANNED": "PLANNED",
        "PLAN": "PLANNED",
        "KẾ HOẠCH": "PLANNED",
        "计划": "PLANNED",

        "RELEASED": "RELEASED",
        "ĐÃ PHÁT HÀNH": "RELEASED",
        "PHÁT HÀNH": "RELEASED",
        "已下达": "RELEASED",

        "RUNNING": "RUNNING",
        "ĐANG CHẠY": "RUNNING",
        "ĐANG SẢN XUẤT": "RUNNING",
        "生产中": "RUNNING",

        "PAUSED": "PAUSED",
        "TẠM DỪNG": "PAUSED",
        "暂停": "PAUSED",

        "COMPLETED": "COMPLETED",
        "HOÀN THÀNH": "COMPLETED",
        "已完成": "COMPLETED",

        "CLOSED": "CLOSED",
        "ĐÃ ĐÓNG": "CLOSED",
        "ĐÓNG": "CLOSED",
        "已关闭": "CLOSED",
    }

    VALID_PRIORITIES = {
        "LOW",
        "NORMAL",
        "HIGH",
        "URGENT",
    }

    PRIORITY_MAPPING = {
        "LOW": "LOW",
        "THẤP": "LOW",
        "低": "LOW",

        "NORMAL": "NORMAL",
        "BÌNH THƯỜNG": "NORMAL",
        "TRUNG BÌNH": "NORMAL",
        "普通": "NORMAL",

        "HIGH": "HIGH",
        "CAO": "HIGH",
        "高": "HIGH",

        "URGENT": "URGENT",
        "KHẨN": "URGENT",
        "GẤP": "URGENT",
        "紧急": "URGENT",
    }

    DEFAULT_STATUS = "PLANNED"
    DEFAULT_PRIORITY = "NORMAL"

    @classmethod
    def normalize_status(cls, value):
        text = str(value or "").strip().upper()

        if not text:
            return cls.DEFAULT_STATUS

        normalized = cls.STATUS_MAPPING.get(
            text,
            text,
        )

        if normalized not in cls.VALID_STATUSES:
            raise ValueError(
                f"Invalid Work Order Status: {value}. "
                "Allowed values: PLANNED, RELEASED, RUNNING, "
                "PAUSED, COMPLETED, CLOSED."
            )

        return normalized

    @classmethod
    def normalize_priority(cls, value):
        text = str(value or "").strip().upper()

        if not text:
            return cls.DEFAULT_PRIORITY

        normalized = cls.PRIORITY_MAPPING.get(
            text,
            text,
        )

        if normalized not in cls.VALID_PRIORITIES:
            raise ValueError(
                f"Invalid Work Order Priority: {value}. "
                "Allowed values: LOW, NORMAL, HIGH, URGENT."
            )

        return normalized

    @classmethod
    def validate_data(cls, data):
        work_order_no = str(
            data.get("work_order_no", "")
        ).strip()

        product_code = str(
            data.get("product_code", "")
        ).strip()

        plan_qty = data.get("plan_qty", 0)
        completed_qty = data.get("completed_qty", 0)
        ng_qty = data.get("ng_qty", 0)

        start_date = data.get("start_date")
        due_date = data.get("due_date")
        finish_date = data.get("finish_date")

        status = data.get(
            "status",
            cls.DEFAULT_STATUS,
        )

        priority = data.get(
            "priority",
            cls.DEFAULT_PRIORITY,
        )

        if not work_order_no:
            raise ValueError(
                "Work Order No is required."
            )

        if not product_code:
            raise ValueError(
                "Product Code is required."
            )

        if len(work_order_no) > 50:
            raise ValueError(
                "Work Order No cannot exceed 50 characters."
            )

        if len(product_code) > 50:
            raise ValueError(
                "Product Code cannot exceed 50 characters."
            )

        try:
            plan_qty = int(plan_qty)
            completed_qty = int(completed_qty)
            ng_qty = int(ng_qty)

        except (TypeError, ValueError) as error:
            raise ValueError(
                "Plan Qty, Completed Qty and NG Qty "
                "must be integers."
            ) from error

        if plan_qty <= 0:
            raise ValueError(
                "Plan Qty must be greater than zero."
            )

        if completed_qty < 0:
            raise ValueError(
                "Completed Qty cannot be negative."
            )

        if ng_qty < 0:
            raise ValueError(
                "NG Qty cannot be negative."
            )

        if completed_qty > plan_qty:
            raise ValueError(
                "Completed Qty cannot exceed Plan Qty."
            )

        if ng_qty > plan_qty:
            raise ValueError(
                "NG Qty cannot exceed Plan Qty."
            )

        if (
            start_date is not None
            and due_date is not None
            and due_date < start_date
        ):
            raise ValueError(
                "Due Date cannot be earlier than Start Date."
            )

        if (
            start_date is not None
            and finish_date is not None
            and finish_date < start_date
        ):
            raise ValueError(
                "Finish Date cannot be earlier than Start Date."
            )

        if status not in cls.VALID_STATUSES:
            raise ValueError(
                f"Invalid Work Order Status: {status}."
            )

        if priority not in cls.VALID_PRIORITIES:
            raise ValueError(
                f"Invalid Work Order Priority: {priority}."
            )

        return True