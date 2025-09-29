from acme.application.interfaces import UnitOfWork
from acme.domain.order import Order
from acme.domain.errors import ValidationError

class OrderService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def place_order(self, lines) -> Order:
        if not lines:
            raise ValidationError("Order needs at least one item.")
        order = Order()
        with self.uow as u:
            for line in lines:
                product = u.products.get_by_id(line.product_id)
                if not product:
                    raise ValidationError(f"Product {line.product_id} not found.")
                product.reserve(line.quantity)
                u.products.update(product)
                order.add_item(
                    product_id=product.id or 0,
                    sku=product.sku,
                    name=product.name,
                    unit_price=product.price,
                    quantity=line.quantity,
                )
            order = u.orders.add(order)
            u.commit()
            return order

    def get_order(self, order_id: int) -> Order:
        order = self.uow.orders.get_by_id(order_id)
        if not order:
            raise ValidationError("Order not found.")
        return order

    def list_orders(self) -> list[Order]:
        return self.uow.orders.list()