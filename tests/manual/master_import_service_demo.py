from src.services.master_import_service import MasterImportService


service = MasterImportService()

print("MasterImportService created successfully.")

try:
    service.preview_product(
        r"D:\File_Not_Exist.xlsx"
    )

except FileNotFoundError as error:
    print("File validation passed:")
    print(error)

print("MasterImportService test passed.")