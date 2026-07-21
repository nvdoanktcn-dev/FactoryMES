import pandas as pd

from src.mapper.production_mapper import ProductionMapper


row = pd.Series({
    "Ngày": "2026-07-10",
    "Tên thiết bị": " bl01 ",
    "Mã công lệnh": " wo001 ",
    "Tên sản phẩm": "product-a",
    "Nhân viên thao tác": "nv001",
    "OP": "op 20",
    "Ca": "Ngày",
    "Thời gian thực tế (H)": 2.5,
    "Thực tế PCS": 120,
    "Tổng NG": 5,
    "Gia công NG": 3,
    "Phôi NG": 2,
})

mapper = ProductionMapper()
data = mapper.map_row(row)

for key, value in data.items():
    print(f"{key}: {value}")