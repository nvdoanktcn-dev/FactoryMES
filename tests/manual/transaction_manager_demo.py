from src.services.master_import.transaction import (
    MemoryTransactionManager,
)

tm = MemoryTransactionManager()

print(
    "Active:",
    tm.in_transaction(),
)

tm.begin()

print(
    "After begin:",
    tm.in_transaction(),
)

tm.commit()

print(
    "After commit:",
    tm.in_transaction(),
)

tm.begin()

tm.rollback()

print(
    "After rollback:",
    tm.in_transaction(),
)

print(
    "TransactionManager OK"
)