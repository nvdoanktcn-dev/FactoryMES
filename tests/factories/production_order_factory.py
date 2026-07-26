from src.models.production_order import ProductionOrder


class ProductionOrderFactory:

    counter = 1

    @classmethod
    def create(cls, session):

        code = f"WO_TEST_{cls.counter:04d}"

        cls.counter += 1

        order = ProductionOrder(

            work_order_no=code,

            product_code="P001",

            operation_no=10,

            operation_name="Test Operation",

            process_type="CNC",

            plan_qty=100,

            completed_qty=0,

            status="PLANNED",

        )

        session.add(order)

        session.flush()

        return order
