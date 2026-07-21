class ImportException(Exception):
    """
    Lỗi cơ sở của Import Engine.
    """


class ImporterNotFoundError(
    ImportException
):
    """
    Không tìm thấy Importer phù hợp.
    """


class ImportExecutionError(
    ImportException
):
    """
    Importer thực thi thất bại.
    """


class ImportTransactionError(
    ImportException
):
    """
    Transaction import thất bại.
    """