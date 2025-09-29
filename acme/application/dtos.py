from dataclasses import dataclass

@dataclass
class CreateProductDTO:
    sku: str
    name: str
    price: str  # parsed into Decimal
    stock: int

@dataclass
class OrderLineDTO:
    product_id: int
    quantity: int