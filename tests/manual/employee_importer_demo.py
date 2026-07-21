from src.importer.employee_importer import EmployeeImporter


FILE_PATH = r"D:\FactoryMES\employee_import_test.xlsx"


importer = EmployeeImporter()

print("=" * 60)
print("PREVIEW")
print("=" * 60)

preview = importer.preview(FILE_PATH)
preview_result = preview["result"]

print("Total   :", preview_result.total)
print("Valid   :", preview_result.valid)
print("Invalid :", preview_result.invalid)

if preview_result.errors:
    print("=" * 60)
    print("PREVIEW ERRORS")
    print("=" * 60)

    for error in preview_result.errors:
        print(error)

assert preview_result.invalid == 0, preview_result.errors


print("=" * 60)
print("IMPORT")
print("=" * 60)

result = importer.import_file(FILE_PATH)

print("=" * 60)
print("ERRORS")
print("=" * 60)

for error in result.errors:
    print(error)

print("Created :", result.created)
print("Updated :", result.updated)
print("Invalid :", result.invalid)

assert result.invalid == 0, result.errors

print("EmployeeImporter test passed.")