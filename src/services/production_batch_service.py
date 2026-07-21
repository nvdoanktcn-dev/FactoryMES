from datetime import datetime

from src.database.session import get_session
from src.framework.exception import NotFoundError, ValidationError
from src.models.production_batch import ProductionBatch
from src.repository.production_batch_repository import (
    ProductionBatchRepository,
)


class ProductionBatchService:
    VALID_STATUSES = {
        "CREATED",
        "PROCESSING",
        "COMPLETED",
        "COMPLETED_WITH_ERRORS",
        "FAILED",
        "ROLLED_BACK",
    }

    def __init__(self, session=None):
        self.session = session if session is not None else get_session()
        self.repository = ProductionBatchRepository(self.session)

    def get_all(self):
        return self.repository.get_all()

    def get_by_batch_no(self, batch_no):
        batch_no = self._normalize_batch_no(batch_no)
        return self.repository.get_by_batch_no(batch_no)

    def get_by_file_hash(self, file_hash):
        if not file_hash:
            return None

        return self.repository.get_by_file_hash(
            str(file_hash).strip().lower()
        )

    def create(
        self,
        import_type,
        file_name,
        file_hash=None,
        imported_by="System",
        remark=None,
    ):
        import_type = str(import_type or "").strip().upper()
        file_name = str(file_name or "").strip()
        imported_by = str(imported_by or "System").strip()

        if not import_type:
            raise ValidationError("Import type is required.")

        if not file_name:
            raise ValidationError("File name is required.")

        if file_hash:
            file_hash = str(file_hash).strip().lower()

            existing = self.repository.get_by_file_hash(file_hash)

            if existing is not None:
                raise ValidationError(
                    f"File already belongs to batch "
                    f"{existing.batch_no}."
                )

        batch = ProductionBatch(
            batch_no=self.generate_batch_no(),
            import_type=import_type,
            file_name=file_name,
            file_hash=file_hash,
            total_rows=0,
            success_rows=0,
            failed_rows=0,
            status="CREATED",
            imported_by=imported_by,
            imported_at=datetime.now(),
            remark=remark,
        )

        return self.repository.add(batch)

    def mark_processing(self, batch_no):
        batch = self._get_required_batch(batch_no)

        if batch.status not in {"CREATED", "FAILED"}:
            raise ValidationError(
                f"Batch {batch.batch_no} cannot change from "
                f"{batch.status} to PROCESSING."
            )

        batch.status = "PROCESSING"
        batch.completed_at = None

        self.repository.update()
        return batch

    def complete(
        self,
        batch_no,
        total_rows,
        success_rows,
        failed_rows,
        remark=None,
    ):
        batch = self._get_required_batch(batch_no)

        total_rows = self._to_non_negative_int(total_rows)
        success_rows = self._to_non_negative_int(success_rows)
        failed_rows = self._to_non_negative_int(failed_rows)

        if success_rows + failed_rows > total_rows:
            raise ValidationError(
                "Success rows plus failed rows cannot exceed total rows."
            )

        batch.total_rows = total_rows
        batch.success_rows = success_rows
        batch.failed_rows = failed_rows
        batch.completed_at = datetime.now()

        if failed_rows == 0:
            batch.status = "COMPLETED"
        elif success_rows > 0:
            batch.status = "COMPLETED_WITH_ERRORS"
        else:
            batch.status = "FAILED"

        if remark is not None:
            batch.remark = str(remark).strip()

        self.repository.update()
        return batch

    def mark_failed(self, batch_no, remark=None):
        batch = self._get_required_batch(batch_no)

        batch.status = "FAILED"
        batch.completed_at = datetime.now()

        if remark is not None:
            batch.remark = str(remark).strip()

        self.repository.update()
        return batch

    def generate_batch_no(self):
        """
        Mã batch dạng:
        PB202607100001
        """
        prefix = datetime.now().strftime("PB%Y%m%d")

        latest = self.repository.get_latest()

        next_sequence = 1

        if latest and latest.batch_no:
            latest_batch_no = str(latest.batch_no).strip().upper()

            if latest_batch_no.startswith(prefix):
                suffix = latest_batch_no[len(prefix):]

                if suffix.isdigit():
                    next_sequence = int(suffix) + 1

        batch_no = f"{prefix}{next_sequence:04d}"

        # Bảo vệ trường hợp dữ liệu cũ không đúng thứ tự id.
        while self.repository.get_by_batch_no(batch_no) is not None:
            next_sequence += 1
            batch_no = f"{prefix}{next_sequence:04d}"

        return batch_no

    def _get_required_batch(self, batch_no):
        batch_no = self._normalize_batch_no(batch_no)
        batch = self.repository.get_by_batch_no(batch_no)

        if batch is None:
            raise NotFoundError(
                f"Production Batch not found: {batch_no}"
            )

        return batch

    @staticmethod
    def _normalize_batch_no(batch_no):
        batch_no = str(batch_no or "").strip().upper()

        if not batch_no:
            raise ValidationError("Batch No is required.")

        return batch_no

    @staticmethod
    def _to_non_negative_int(value):
        try:
            number = int(value or 0)
        except (TypeError, ValueError) as error:
            raise ValidationError(
                f"Invalid integer value: {value}"
            ) from error

        if number < 0:
            raise ValidationError(
                f"Value cannot be negative: {value}"
            )

        return number