from src.importer.machine_importer import (
    MachineImporter,
)

FILE_PATH = r"D:\FactoryMES\machine_import_test.xlsx"

importer = MachineImporter()

print("=" * 60)
print("PREVIEW")
print("=" * 60)

preview = importer.preview(FILE_PATH)

result = preview["result"]

print(result.total)
print(result.valid)
print(result.invalid)

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

print()

assert result.invalid == 0, result.errors
print("MachineImporter test passed.")