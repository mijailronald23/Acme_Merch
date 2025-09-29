from decimal import Decimal
import pytest
from acme.domain.product import Product
from acme.domain.order import Order, OrderItem
from acme.domain.errors import OutOfStock, ValidationError

def test_product_reserve_and_validation():
    p = Product(id=1, sku="A", name="Item A", price=Decimal("10.00"), stock=5)
    p.validate()
    p.reserve(3)
    assert p.stock == 2

def test_reserve_out_of_stock():
    p = Product(id=1, sku="A", name="Item A", price=Decimal("10.00"), stock=1)
    with pytest.raises(OutOfStock):
        p.reserve(2)

def test_order_total_rounding():
    o = Order(items=[OrderItem(1,"A","Item A",Decimal("5.555"),2)])
    assert o.total == Decimal("11.11")
