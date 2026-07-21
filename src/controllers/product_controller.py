from src.services.product_service import ProductService


class ProductController:
    def __init__(self):
        self.service = ProductService()

    def get_all_products(self):
        return self.service.get_all_products()

    def get_product(self, product_code):
        return self.service.get_product(product_code)

    def search_products(self, keyword):
        return self.service.search_products(keyword)

    def create_product(self, data):
        return self.service.create_product(**data)

    def update_product(self, product_code, data):
        return self.service.update_product(product_code, data)

    def delete_product(self, product_code):
        return self.service.delete_product(product_code)