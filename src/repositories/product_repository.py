from __future__ import annotations

from src.repositories.base_repository import BaseRepository


class ProductRepository(BaseRepository):
    """
    In-memory Product Repository.
    """

    def __init__(self):
        self.storage = {}

    # -------------------------------------------------

    def insert_batch(self, entities):

        for entity in entities or []:

            key = self._normalize(entity.product_code)

            if key in self.storage:
                raise ValueError(
                    f"Product already exists: {key}"
                )

            self.storage[key] = entity

        return len(entities or [])

    # -------------------------------------------------

    def update_batch(self, entities):

        for entity in entities or []:

            key = self._normalize(entity.product_code)

            self.storage[key] = entity

        return len(entities or [])

    # -------------------------------------------------

    def delete_batch(self, entities):

        deleted = 0

        for entity in entities or []:

            key = self._normalize(entity.product_code)

            if self.storage.pop(key, None):

                deleted += 1

        return deleted

    # -------------------------------------------------

    def exists(self, key):

        return self._normalize(key) in self.storage

    # -------------------------------------------------

    def get(self, key):

        return self.storage.get(
            self._normalize(key)
        )

    # -------------------------------------------------

    def get_all(self):

        return list(
            self.storage.values()
        )

    # -------------------------------------------------

    def count(self):

        return len(
            self.storage
        )

    # -------------------------------------------------

    def clear(self):

        self.storage.clear()

    # -------------------------------------------------
    def get_by_code(self, product_code):
        return self.get(product_code)

    def add(self, entity):
        self.storage[self._normalize(entity.product_code)] = entity
        return entity

    def update(self):
        # Repository in-memory cập nhật trực tiếp object,
        # nên không cần thao tác gì thêm.
        return   

    @staticmethod
    def _normalize(key):

        key = str(key).strip().upper()

        if not key:
            raise ValueError(
                "Product Code is empty."
            )

        return key