from .product_repository import (
    ProductRepository,
)


class RepositoryFactory:

    _repositories = {

        "PRODUCT":
            ProductRepository(),

    }

    @classmethod
    def get(
        cls,
        module_name,
    ):

        return cls._repositories[
            module_name.upper()
        ]