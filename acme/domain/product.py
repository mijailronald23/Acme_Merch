from dataclasses import dataclass
from decimal import Decimal
from .errors import ValidationError, OutOfStock

@dataclass
class Product:
    id: int | None
    sku: str
    name: str
    price: Decimal
    stock: int

    def validate(self):
        if self.price < Decimal("0"):
            raise ValidationError("Price cannot be negative.")
        if self.stock < 0:
            raise ValidationError("Stock cannot be negative.")
        if not self.sku or not self.name:
            raise ValidationError("SKU and name are required.")

    def reserve(self, qty: int):
        if qty <= 0:
            raise ValidationError("Quantity must be >= 1.")
        if qty > self.stock:
            raise OutOfStock(f"Not enough stock for {self.sku}.")
        self.stock -= qty