from src.services.production_batch_service import (
    ProductionBatchService,
)


service = ProductionBatchService()

batch = service.create(
    import_type="CNC",
    file_name="CNC_TEST.xlsx",
    file_hash="test-hash-001",
    imported_by="System",
)

print("Created:", batch.batch_no, batch.status)

service.mark_processing(batch.batch_no)

batch = service.complete(
    batch_no=batch.batch_no,
    total_rows=10,
    success_rows=10,
    failed_rows=0,
)

print(
    "Completed:",
    batch.batch_no,
    batch.status,
    batch.total_rows,
    batch.success_rows,
    batch.failed_rows,
)