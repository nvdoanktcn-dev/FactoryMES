from src.services.production_import_service import ProductionImportService


FILE_PATH = r"D:\Data\CNC_TEST.xlsx"


def main() -> None:
    service = ProductionImportService()

    try:
        preview = service.preview_cnc(FILE_PATH)

        print("Rows:", preview["rows"])
        print("Mapped:", preview["mapped"])
        print("Failed:", preview["failed"])

        for error in preview["errors"][:10]:
            print(error)

    finally:
        close = getattr(service, "close", None)
        if callable(close):
            close()


if __name__ == "__main__":
    main()