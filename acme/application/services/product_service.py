from decimal import Decimal
from acme.domain.product import Product
from acme.application.interfaces import UnitOfWork
from acme.domain.errors import ValidationError

class ProductService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def create(self, dto) -> Product:
        p = Product(
            id=None,
            sku=dto.sku.strip(),
            name=dto.name.strip(),
            price=Decimal(dto.price),
            stock=int(dto.stock),
        )
        p.validate()
        with self.uow as u:
            if u.products.get_by_sku(p.sku):
                raise ValidationError("SKU already exists.")
            p = u.products.add(p)
            u.commit()
            return p

    def list(self) -> list[Product]:
        return self.uow.products.list()

    def update(self, id: int, dto) -> Product:
        with self.uow as u:
            existing = u.products.get_by_id(id)
            if not existing:
                raise ValidationError("Product not found.")
            new_sku = dto.sku.strip()
            if new_sku != existing.sku and u.products.get_by_sku(new_sku):
                raise ValidationError("SKU already exists.")
            existing.sku = new_sku
            existing.name = dto.name.strip()
            existing.price = Decimal(dto.price)
            existing.stock = int(dto.stock)
            existing.validate()
            u.products.update(existing)
            u.commit()
            return existing