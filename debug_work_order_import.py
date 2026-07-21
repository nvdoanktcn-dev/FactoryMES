import sys
import traceback

from src.importer.work_order_importer import WorkOrderImporter


if len(sys.argv) < 2:
    print(
        "Usage: python debug_work_order_import.py "
        '"D:\\path\\work_order.xlsx"'
    )
    raise SystemExit(1)


file_path = sys.argv[1]

try:
    importer = WorkOrderImporter()

    print("=" * 70)
    print("PREVIEW")
    print("=" * 70)

    preview = importer.preview(file_path)
    result = preview["result"]
    errors = preview.get(
        "errors",
        result.errors,
    )

    print("File    :", file_path)
    print("Total   :", result.total)
    print("Valid   :", result.valid)
    print("Invalid :", result.invalid)

    if errors:
        print("=" * 70)
        print("PREVIEW ERRORS")
        print("=" * 70)

        for error in errors:
            print(error)

    if errors:
        raise SystemExit(
            "Preview contains errors. Import stopped."
        )

    print("=" * 70)
    print("IMPORT")
    print("=" * 70)

    import_result = importer.import_file(
        file_path
    )

    print("Created :", import_result.created)
    print("Updated :", import_result.updated)
    print("Skipped :", import_result.skipped)
    print("Invalid :", import_result.invalid)

    if import_result.errors:
        print("=" * 70)
        print("IMPORT ERRORS")
        print("=" * 70)

        for error in import_result.errors:
            print(error)

except Exception:
    print("=" * 70)
    print("UNHANDLED ERROR")
    print("=" * 70)
    traceback.print_exc()