from src.importer.work_order_importer import WorkOrderImporter


FILE_PATH = r"D:\FactoryMES\work_order_import_test.xlsx"


def main() -> None:
    importer = WorkOrderImporter()

    try:
        print("=" * 60)
        print("PREVIEW")
        print("=" * 60)

        preview = importer.preview(FILE_PATH)
        result = preview["result"]

        print("Total   :", result.total)
        print("Valid   :", result.valid)
        print("Invalid :", result.invalid)

        errors = preview.get("errors", [])

        for error in errors:
            print(error)

        assert not errors, errors

        print("=" * 60)
        print("IMPORT")
        print("=" * 60)

        result = importer.import_file(FILE_PATH)

        print("Created :", result.created)
        print("Updated :", result.updated)
        print("Invalid :", result.invalid)

        for error in result.errors:
            print(error)

        assert result.invalid == 0, result.errors

        print()
        print("WorkOrderImporter test passed.")

    finally:
        close = getattr(importer, "close", None)

        if callable(close):
            close()


if __name__ == "__main__":
    main()