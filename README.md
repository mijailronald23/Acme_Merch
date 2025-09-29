# Acme Merch — Clean Architecture Django (MVP)

A small service for **Acme Merch** to manage a product catalog and accept customer orders. Built with **Django + DRF** following **Clean Architecture** boundaries.


## WSL‑friendly Quickstart

```bash
# 1) Create & activate a fresh venv (inside WSL)
python3 -m venv .venv && source .venv/bin/activate

# 2) Install
pip install -U pip setuptools wheel
pip install "Django==5.1.2" djangorestframework drf-spectacular

# 3) Migrate & run
python manage.py makemigrations infrastructure
python manage.py migrate
python manage.py runserver

# 4) Use it
# Docs (Swagger): http://127.0.0.1:8000/docs/
# API root:       http://127.0.0.1:8000/api/
# Simple HTML form to create products: http://127.0.0.1:8000/api/product-form/

# 5) (Optional) Quick seed via shell
python manage.py shell -c "from acme.infrastructure.django_impl.models import ProductModel as P; P.objects.create(sku='SKU-ABC', name='Bottle', price='29.90', stock=10)"

```

**Defaults**: `LANGUAGE_CODE = "en-us"`, `TIME_ZONE = "UTC"`, DB = SQLite (dev).

---

## Architecture (Clean boundaries)

```
acme/
├─ domain/           # Entities & business rules (pure Python, no Django)
│  ├─ product.py     # Product entity: invariants, reserve()
│  ├─ order.py       # Order & OrderItem: totals calculation
│  └─ errors.py      # DomainError, ValidationError, OutOfStock
├─ application/      # Use cases (services) & ports (interfaces)
│  ├─ services/
│  │  ├─ product_service.py  # create/list/update product
│  │  └─ order_service.py    # place_order, get_order, list_orders
│  ├─ interfaces.py  # ProductRepository, OrderRepository, UnitOfWork
│  └─ dtos.py        # DTOs for input data
└─ infrastructure/   # Adapters (Django ORM implementations)
   └─ django_impl/
      ├─ apps.py
      ├─ models.py           # ProductModel, OrderModel, OrderItemModel
      └─ repositories.py     # Django*Repository + UnitOfWork
webapi/               # Web/API layer (DRF), HTML forms for demo
├─ views.py           # ProductViewSet, OrderListView, OrderDetailView
├─ serializers.py     # API DTOs, explicit request/response
└─ templates/webapi/  # product_form.html, order_form.html (CSRF-safe)
config/               # Django settings/urls (OpenAPI enabled)
```

**Dependency rule:** `webapi` → `application` → `domain`. `infrastructure` implements `application` ports; upper layers depend on **interfaces**, not concrete Django models.

---

## Domain Model & Rules (explicit)

**Entities**
- **Product**: `id, sku, name, price: Decimal(2), stock: int`
- **Order**: `id, items: list[OrderItem]`, with computed `total`
- **OrderItem**: snapshot (product_id, sku, name, unit_price, quantity)

**Business rules (in Domain)**
- Price ≥ 0; Stock ≥ 0; SKU and name required.
- **Stock policy:** no negative stock. Reserve (decrement) at order placement. No backorders.
- **Pricing:** total = Σ(unit_price × qty) using `Decimal`, rounded to 2 decimals.

**Transaction boundary:** one atomic transaction per order (all-or-nothing).

**IDs:** Auto-increment integers (simple, DB-friendly for MVP).

---

## Use Cases (Application layer)

- **Create product** (command)
- **Update product** (command)
- **List products** (query)
- **Place order** (command: validates & reserves stock, persists order)
- **Get order** (query: returns items + calculated total)

**Services:** `ProductService`, `OrderService` use a `UnitOfWork` with repository interfaces. Domain errors propagate as typed exceptions.

---

## Persistence (Infrastructure)

- Django ORM models (`ProductModel`, `OrderModel`, `OrderItemModel`).
- Repositories map ORM ↔ domain and return **domain objects** only (no ORM leakage).
- `DjangoUnitOfWork` uses `transaction.atomic()`; commit flag controls rollback.

---

## API (Web)

**OpenAPI/Swagger** at `/docs`, schema at `/schema`.

### Endpoints
- `GET /api/products/` → list products
- `POST /api/products/` → create product `{sku, name, price, stock}`
- `PUT /api/products/{id}/` → update product
- `POST /api/orders/` → place order `{items:[{product_id, quantity}]}`
- `GET /api/orders/{id}/` → get order with items & `total`

**Example**: Create product
```json
{
  "sku": "SKU-ABC",
  "name": "Bottle",
  "price": "29.90",
  "stock": 10
}
```

**Example**: Place order
```json
{
  "items": [ { "product_id": 1, "quantity": 2 } ]
}
```

---

## Error Handling (documented policy)

**Domain errors → HTTP**
- `ValidationError` → **400 Bad Request** (`{"detail": "..."}`)
- `OutOfStock` → **400 Bad Request** (MVP). *(Could be 409 Conflict if preferred.)*
- Missing order → **404 Not Found**

**Parse/serializer errors** → 400 (DRF default).

> Optionally wire a DRF `EXCEPTION_HANDLER` to map exceptions globally. For MVP, views already catch `DomainError` and return JSON `{detail}` with appropriate status.

---

## Testing Strategy

**Core focus:** rules testable without web/DB.

- **Domain tests**: product validation & reserve, order total.
- **Application tests**: place order decrements stock & computes total using **fake repos/UoW**.
- (Optional) **API tests**: happy paths + common errors.

Run:
```bash
python manage.py test
```

---



## Compliance Matrix (Core Requirements)

| Area | Requirement | Status | Where |
|---|---|---|---|
| Domain | Products entity & invariants | ✅ Done | `acme/domain/product.py` |
| Domain | Orders & OrderItems + pricing | ✅ Done | `acme/domain/order.py` |
| Domain | Stock check on order | ✅ Done | `Product.reserve()` + `OrderService` |
| Use Cases | Create/Update/List products | ✅ Done | `ProductService`, `webapi/views.py` |
| Use Cases | Place order | ✅ Done | `OrderService.place_order` |
| Use Cases | Get order details w/ totals | ✅ Done | `OrderService.get_order` |
| Architecture | Clean boundaries & dependency rule | ✅ Done | folder structure & service/repo pattern |
| Architecture | Command vs Query separation | ✅ Minimal | separate methods; services split |
| Persistence | Relational DB via Django ORM | ✅ Done | `infrastructure/django_impl` |
| Persistence | Repos expose domain objects | ✅ Done | `repositories.py` |
| API | Minimal REST + Swagger | ✅ Done | DRF + Spectacular (`/docs`) |
| API | Error handling strategy documented | ✅ Done | README + view try/except |
| Testing | Domain and application tests | ✅ Done | `tests/` |
| Non‑functional | Readability & boundaries | ✅ Done | Structure above |
| Non‑functional | Testability (no web/DB) | ✅ Done | Domain/App tests |
| Non‑functional | Observability (light logs) | ⚠️ Add | suggest logger in views |
| Non‑functional | Performance (reasonable) | ✅ Done | simple queries |

---

## Ambiguity Decisions (explicit)

- **Currency & rounding:** USD, two decimals, `Decimal` with `quantize(0.01)`.
- **Stock behavior:** no negative stock; deduct on order; no backorders.
- **IDs:** auto-increment ints (simplicity for MVP).
- **Validation location:** domain (entities) + app (use-case orchestration); API serializes inputs.
- **Transactions:** one atomic transaction per order.
- **Auth:** not required (MVP). Endpoints are open in dev.
- **DTO mapping:** manual.
- **Repositories:** specific interfaces (Product/Order) rather than generic.

---

## Stretch Goals (choose a few)

**Not all implemented**—here’s what’s practical next:

1) **Seed data** (simple management command or fixture) — *recommended for demos*.
2) **CI (GitHub Actions)**: run `black`/`ruff` + `pytest` on push.
3) **Idempotent order creation** via `Idempotency-Key` header (store last response by key, return same on retry).
4) **Cache** `GET /api/products/` (e.g., `@cache_page(60)`).
5) **Docker compose** for Postgres (optional; SQLite is enough for MVP).

> Pick 2–3 for polish; 1 & 2 are the quickest wins for presentation.

---

## Demo Script (2–3 minutes)

1. Open **/docs** → show endpoints & schema.
2. **Create Product** with Try-it-Out (SKU, name, price, stock).
3. **List Products** to see it.
4. **Place Order** with `{ items: [{ product_id, quantity }] }`.
5. **Get Order** by id → point out line totals and `total`.
6. Optional: show **/api/product-form/** (simple HTML form) for non-cURL demos.

---

## How to Run Tests & Lint 

```bash
python manage.py test
# if you add ruff/black:
pip install ruff black
ruff check . && black --check .
```

---

## Known Limitations

- No pagination/filters on products.
- No auth or rate limiting.
- No concurrency control on stock beyond a single DB tx.
- No idempotency for duplicate order submissions (yet).

---

## Appendix — Error Mapping Examples

- `POST /api/orders/` with qty > stock → `400 {"detail": "Not enough stock for ..."}`
- `GET /api/orders/999` (missing) → `404 {"detail": "Order not found."}`
- Serializer error (e.g., missing field) → `400` with field errors.


