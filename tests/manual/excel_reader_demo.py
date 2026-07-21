import sys

from src.services.master_import import (
    ExcelReaderService,
)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(
            "Usage: python test_excel_reader.py "
            "<excel_file_path>"
        )

    file_path = sys.argv[1]

    service = ExcelReaderService()

    sheet_names = service.inspect_workbook(
        file_path
    )

    print("=" * 70)
    print("EXCEL READER")
    print("=" * 70)

    print(
        "Sheets:",
        sheet_names,
    )

    result = service.preview(
        file_path=file_path,
        limit=10,
    )

    print(
        "Selected sheet:",
        result.sheet_name,
    )

    print(
        "Header row:",
        result.header_row + 1,
    )

    print(
        "Headers:",
        result.headers,
    )

    print(
        "Total rows:",
        result.total_rows,
    )

    print(
        "Preview rows:",
        len(result.rows),
    )

    for row in result.rows[:3]:
        print(row)

    print()
    print(
        "ExcelReaderService test passed."
    )


if __name__ == "__main__":
    main()