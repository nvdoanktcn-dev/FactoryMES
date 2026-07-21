from src.importer.routing_importer import RoutingImporter


FILE_PATH = r"D:\FactoryMES\routing_import_test.xlsx"


def main() -> None:
    importer = RoutingImporter()

    try:
        print("=" * 60)
        print("PREVIEW")
        print("=" * 60)

        preview = importer.preview(FILE_PATH)
        preview_result = preview["result"]

        print("Total   :", preview_result.total)
        print("Valid   :", preview_result.valid)
        print("Invalid :", preview_result.invalid)

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

        print("RoutingImporter test passed.")

    finally:
        close = getattr(importer, "close", None)

        if callable(close):
            close()


if __name__ == "__main__":
    main()