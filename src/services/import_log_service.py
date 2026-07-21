from src.database.session import get_session
from src.models.import_log import ImportLog
from src.repository.import_log_repository import ImportLogRepository


class ImportLogService:
    def __init__(self):
        self.session = get_session()
        self.repository = ImportLogRepository(self.session)

    def get_by_hash(self, file_hash):
        return self.repository.get_by_hash(file_hash)

    def exists(self, file_hash):
        return self.get_by_hash(file_hash) is not None

    def create(
        self,
        file_name,
        file_hash,
        import_type,
        total,
        success,
        failed,
        imported_by="System",
        remark=None,
    ):
        existing = self.repository.get_by_hash(file_hash)

        if existing is not None:
            return existing

        log = ImportLog(
            file_name=file_name,
            file_hash=file_hash,
            import_type=import_type,
            total_rows=total,
            success_rows=success,
            failed_rows=failed,
            imported_by=imported_by,
            remark=remark,
        )

        return self.repository.add(log)