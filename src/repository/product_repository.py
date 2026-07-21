from src.models.product import Product
from src.repository.base_repository import BaseRepository


class ProductRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session, Product)

    def get_by_code(self, product_code):
        return (
            self.session.query(Product)
            .filter(Product.product_code == product_code)
            .first()
        )