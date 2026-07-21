class ImportResult:
    def __init__(self):
        self.total = 0
        self.success = 0
        self.failed = 0
        self.errors = []

    def add_success(self):
        self.success += 1

    def add_error(self, row, message):
        self.failed += 1
        self.errors.append({
            "row": row,
            "message": message
        })

    def finish(self, total):
        self.total = total