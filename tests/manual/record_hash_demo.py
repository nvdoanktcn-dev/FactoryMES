from src.utils.production_hash import (
    create_production_record_hash,
)


record_1 = {
    "work_order_no": "WO001",
    "product_code": "P001",
    "op_no": "OP10",
    "machine_code": "BL01",
    "employee_code": "NV001",
    "shift": "DAY",
    "start_time": None,
    "finish_time": None,
    "run_time_sec": 3600,
    "ok_qty": 100,
    "ng_qty": 2,
}

record_2 = dict(record_1)

hash_1 = create_production_record_hash(record_1)
hash_2 = create_production_record_hash(record_2)

print("Hash 1:", hash_1)
print("Hash 2:", hash_2)
print("Same:", hash_1 == hash_2)

record_2["ok_qty"] = 101

hash_3 = create_production_record_hash(record_2)

print("Hash 3:", hash_3)
print("Changed:", hash_1 != hash_3)