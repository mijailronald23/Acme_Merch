from decimal import Decimal
from django.db import transaction
from acme.application.interfaces import ProductRepository, OrderRepository, UnitOfWork
from acme.domain.product import Product
from acme.domain.order import Order, OrderItem
from .models import ProductModel, OrderModel, OrderItemModel

# ----- mappers -----
def product_to_domain(m: ProductModel) -> Product:
    return Product(id=m.id, sku=m.sku, name=m.name, price=Decimal(m.price), stock=m.stock)

def order_to_domain(om: OrderModel) -> Order:
    items = [
        OrderItem(
            product_id=i.product_id, sku=i.sku, name=i.name,
            unit_price=Decimal(i.unit_price), quantity=i.quantity
        ) for i in om.items.all()
    ]
    return Order(id=om.id, items=items)

# ----- repositories -----
class DjangoProductRepository(ProductRepository):
    def add(self, p: Product) -> Product:
        m = ProductModel.objects.create(sku=p.sku, name=p.name, price=p.price, stock=p.stock)
        return product_to_domain(m)

    def update(self, p: Product) -> None:
        ProductModel.objects.filter(id=p.id).update(
            sku=p.sku, name=p.name, price=p.price, stock=p.stock
        )

    def get_by_id(self, id: int) -> Product | None:
        m = ProductModel.objects.filter(id=id).first()
        return product_to_domain(m) if m else None

    def get_by_sku(self, sku: str) -> Product | None:
        m = ProductModel.objects.filter(sku=sku).first()
        return product_to_domain(m) if m else None

    def list(self) -> list[Product]:
        return [product_to_domain(m) for m in ProductModel.objects.all().order_by("id")]

class DjangoOrderRepository(OrderRepository):
    def add(self, o: Order) -> Order:
        om = OrderModel.objects.create()
        bulk = []
        for i in o.items:
            pm = ProductModel.objects.get(id=i.product_id)
            bulk.append(OrderItemModel(
                order=om, product=pm, sku=i.sku, name=i.name,
                unit_price=i.unit_price, quantity=i.quantity
            ))
        OrderItemModel.objects.bulk_create(bulk)
        # reload with items to avoid incomplete return
        om = OrderModel.objects.prefetch_related("items").get(id=om.id)
        return order_to_domain(om)

    def get_by_id(self, id: int) -> Order | None:
        om = OrderModel.objects.filter(id=id).prefetch_related("items").first()
        return order_to_domain(om) if om else None

    def list(self) -> list[Order]:
        q = OrderModel.objects.all().prefetch_related("items").order_by("id")
        return [order_to_domain(om) for om in q]

# ----- Unit of Work -----
class DjangoUnitOfWork(UnitOfWork):
    def __init__(self):
        self.products = DjangoProductRepository()
        self.orders = DjangoOrderRepository()
        self._atomic = None
        self._committed = False

    def __enter__(self):
        self._atomic = transaction.atomic()
        self._ctx = self._atomic.__enter__()
        self._committed = False
        return self

    def commit(self) -> None:
        self._committed = True  # commit happens at __exit__ if no rollback

    def __exit__(self, exc_type, exc, tb):
        if not self._committed and self._atomic:
            transaction.set_rollback(True)
        return self._atomic.__exit__(exc_type, exc, tb)