from decimal import Decimal
from acme.domain.product import Product
from acme.application.services.order_service import OrderService
from acme.application.dtos import OrderLineDTO

class FakeProductRepo:
    def __init__(self, data): self.data = {p.id: p for p in data}
    def add(self, p): ...
    def update(self, p): self.data[p.id] = p
    def get_by_id(self, id): return self.data.get(id)
    def get_by_sku(self, sku): ...
    def list(self): return list(self.data.values())

class FakeOrderRepo:
    def __init__(self): self.data = {}; self._id = 0
    def add(self, o): self._id += 1; o.id = self._id; self.data[o.id] = o; return o
    def get_by_id(self, id): return self.data.get(id)

class FakeUoW:
    def __init__(self, products, orders): self.products=products; self.orders=orders
    def __enter__(self): return self
    def __exit__(self,*a): ...
    def commit(self): ...

def test_place_order_decreases_stock_and_calculates_total():
    p = Product(id=1, sku="A", name="Item A", price=Decimal("10.00"), stock=5)
    svc = OrderService(FakeUoW(FakeProductRepo([p]), FakeOrderRepo()))
    order = svc.place_order([OrderLineDTO(product_id=1, quantity=3)])
    assert order.total == Decimal("30.00")
    assert svc.uow.products.get_by_id(1).stock == 2