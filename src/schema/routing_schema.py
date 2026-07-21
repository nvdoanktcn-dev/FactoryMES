class RoutingSchema:
    """
    Cấu trúc dữ liệu chuẩn cho Routing Master Import.

    Schema chịu trách nhiệm:
    - Mapping tên cột Excel
    - Chuẩn hóa giá trị đơn giản
    - Kiểm tra kiểu dữ liệu cơ bản

    Schema không truy cập database.
    """

    REQUIRED_COLUMNS = [
        "Product Code",
        "OP No",
        "Sequence",
        "Machine Code",
        "Cycle Time Sec",
    ]

    OPTIONAL_COLUMNS = [
        "OP Name",
        "Process Type",
        "Machine Type",
        "Setup Time Min",
        "Standard Output Hour",
        "Status",
        "Remark",
    ]

    COLUMN_MAPPING = {
        # Product
        "Product Code": "Product Code",
        "Mã sản phẩm": "Product Code",
        "Mã hàng": "Product Code",
        "产品编码": "Product Code",
        "产品代码": "Product Code",

        # Operation
        "OP No": "OP No",
        "OP": "OP No",
        "Công đoạn": "OP No",
        "Mã công đoạn": "OP No",
        "工序": "OP No",
        "工序编号": "OP No",

        "OP Name": "OP Name",
        "Tên công đoạn": "OP Name",
        "Tên OP": "OP Name",
        "工序名称": "OP Name",

        # Sequence
        "Sequence": "Sequence",
        "Thứ tự": "Sequence",
        "Trình tự": "Sequence",
        "顺序": "Sequence",
        "序号": "Sequence",

        # Process
        "Process Type": "Process Type",
        "Loại công đoạn": "Process Type",
        "Loại gia công": "Process Type",
        "工艺类型": "Process Type",

        # Machine
        "Machine Type": "Machine Type",
        "Loại máy": "Machine Type",
        "设备类型": "Machine Type",

        "Machine Code": "Machine Code",
        "Mã máy": "Machine Code",
        "Mã thiết bị": "Machine Code",
        "设备编码": "Machine Code",
        "机台编号": "Machine Code",

        # Time
        "Cycle Time Sec": "Cycle Time Sec",
        "Cycle Time": "Cycle Time Sec",
        "Chu kỳ (giây)": "Cycle Time Sec",
        "Thời gian chu kỳ": "Cycle Time Sec",
        "周期时间": "Cycle Time Sec",

        "Setup Time Min": "Setup Time Min",
        "Setup Time": "Setup Time Min",
        "Thời gian setup": "Setup Time Min",
        "准备时间": "Setup Time Min",

        "Standard Output Hour": "Standard Output Hour",
        "Sản lượng chuẩn/giờ": "Standard Output Hour",
        "Tiêu chuẩn sản lượng giờ": "Standard Output Hour",
        "每小时标准产量": "Standard Output Hour",

        # Status
        "Status": "Status",
        "Trạng thái": "Status",
        "状态": "Status",

        # Remark
        "Remark": "Remark",
        "Ghi chú": "Remark",
        "备注": "Remark",
    }

    VALID_MACHINE_TYPES = {
        "CNC",
        "ROBOT",
        "MANUAL",
        "INSPECTION",
        "OTHER",
    }

    VALID_STATUSES = {
        "ACTIVE",
        "INACTIVE",
    }

    STATUS_MAPPING = {
        "ACTIVE": "ACTIVE",
        "HOẠT ĐỘNG": "ACTIVE",
        "ĐANG HOẠT ĐỘNG": "ACTIVE",
        "启用": "ACTIVE",
        "有效": "ACTIVE",
        "1": "ACTIVE",

        "INACTIVE": "INACTIVE",
        "NGỪNG HOẠT ĐỘNG": "INACTIVE",
        "KHÔNG HOẠT ĐỘNG": "INACTIVE",
        "停用": "INACTIVE",
        "无效": "INACTIVE",
        "0": "INACTIVE",
    }

    MACHINE_TYPE_MAPPING = {
        "CNC": "CNC",
        "MÁY CNC": "CNC",
        "数控": "CNC",

        "ROBOT": "ROBOT",
        "MÁY ROBOT": "ROBOT",
        "机器人": "ROBOT",

        "MANUAL": "MANUAL",
        "THỦ CÔNG": "MANUAL",
        "手工": "MANUAL",

        "INSPECTION": "INSPECTION",
        "KIỂM TRA": "INSPECTION",
        "检测": "INSPECTION",

        "OTHER": "OTHER",
        "KHÁC": "OTHER",
        "其他": "OTHER",
    }

    DEFAULT_STATUS = "ACTIVE"

    @classmethod
    def normalize_status(cls, value):
        text = str(value or "").strip().upper()

        if not text:
            return cls.DEFAULT_STATUS

        status = cls.STATUS_MAPPING.get(text, text)

        if status not in cls.VALID_STATUSES:
            raise ValueError(
                f"Invalid Routing Status: {value}. "
                "Allowed values: ACTIVE, INACTIVE."
            )

        return status

    @classmethod
    def normalize_machine_type(cls, value, machine_code=""):
        text = str(value or "").strip().upper()

        if not text:
            return cls.infer_machine_type(machine_code)

        machine_type = cls.MACHINE_TYPE_MAPPING.get(
            text,
            text,
        )

        if machine_type not in cls.VALID_MACHINE_TYPES:
            raise ValueError(
                f"Invalid Machine Type: {value}."
            )

        return machine_type

    @staticmethod
    def infer_machine_type(machine_code):
        code = str(machine_code or "").strip().upper()

        if code.startswith("BL"):
            return "CNC"

        if code.startswith("BR"):
            return "ROBOT"

        if code.startswith("ASK"):
            return "ROBOT"

        return "OTHER"

    @staticmethod
    def normalize_op(value):
        text = str(value or "").strip().upper()

        if not text:
            return ""

        digits = "".join(
            character
            for character in text
            if character.isdigit()
        )

        if digits:
            return f"OP{int(digits)}"

        return text

    @classmethod
    def validate_data(cls, data):
        product_code = str(
            data.get("product_code", "")
        ).strip()

        op_no = str(
            data.get("op_no", "")
        ).strip()

        machine_code = str(
            data.get("machine_code", "")
        ).strip()

        sequence = data.get("sequence", 0)
        cycle_time_sec = data.get("cycle_time_sec", 0)
        setup_time_min = data.get("setup_time_min", 0)
        standard_output_hour = data.get(
            "standard_output_hour",
            0,
        )

        if not product_code:
            raise ValueError("Product Code is required.")

        if not op_no:
            raise ValueError("OP No is required.")

        if not machine_code:
            raise ValueError("Machine Code is required.")

        if not op_no.startswith("OP"):
            raise ValueError(
                f"Invalid OP format: {op_no}"
            )

        if int(sequence) <= 0:
            raise ValueError(
                "Sequence must be greater than zero."
            )

        if float(cycle_time_sec) <= 0:
            raise ValueError(
                "Cycle Time Sec must be greater than zero."
            )

        if float(setup_time_min) < 0:
            raise ValueError(
                "Setup Time Min cannot be negative."
            )

        if float(standard_output_hour) < 0:
            raise ValueError(
                "Standard Output Hour cannot be negative."
            )

        machine_type = data.get("machine_type")

        if machine_type not in cls.VALID_MACHINE_TYPES:
            raise ValueError(
                f"Invalid Machine Type: {machine_type}"
            )

        status = data.get("status")

        if status not in cls.VALID_STATUSES:
            raise ValueError(
                f"Invalid Routing Status: {status}"
            )

        return True