import pandas as pd


data = [
    {
        "Mã sản phẩm": "P001",
        "Tên sản phẩm": "Sản phẩm thử nghiệm 1",
        "Tên sản phẩm CN": "测试产品1",
        "Khách hàng": "Customer A",
        "Vật liệu": "AL6061",
        "Đơn vị": "PCS",
        "Trạng thái": "ACTIVE",
        "Ghi chú": "Created by import test",
    },
    {
        "Mã sản phẩm": "P002",
        "Tên sản phẩm": "Sản phẩm thử nghiệm 2",
        "Tên sản phẩm CN": "测试产品2",
        "Khách hàng": "Customer B",
        "Vật liệu": "SUS304",
        "Đơn vị": "",
        "Trạng thái": "",
        "Ghi chú": "",
    },
]


dataframe = pd.DataFrame(data)

output_file = "product_import_test.xlsx"

dataframe.to_excel(
    output_file,
    index=False,
)

print(f"Created: {output_file}")