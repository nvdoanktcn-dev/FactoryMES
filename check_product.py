from src.database.session import get_session
from src.models.product import Product

session = get_session()

products = session.query(Product).all()

print(f"Tổng số Product: {len(products)}")

for p in products:
    print(p.product_code, p.product_name_vi)