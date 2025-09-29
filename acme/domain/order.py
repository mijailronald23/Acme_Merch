from dataclasses import dataclass, field
from decimal import Decimal
from .errors import ValidationError

@dataclass
class OrderItem:
    product_id: int
    sku: str
    name: str
    unit_price: Decimal
    quantity: int

    @property
    def line_total(self) -> Decimal:
        return (self.unit_price * self.quantity).quantize(Decimal("0.01"))

@dataclass
class Order:
    id: int | None = None
    items: list[OrderItem] = field(default_factory=list)

    def add_item(self, *, product_id: int, sku: str, name: str, unit_price: Decimal, quantity: int):
        if quantity <= 0:
            raise ValidationError("Quantity must be >= 1.")
        self.items.append(OrderItem(product_id, sku, name, unit_price, quantity))

    @property
    def total(self) -> Decimal:
        total = sum((i.line_total for i in self.items), Decimal("0"))
        return total.quantize(Decimal("0.01"))