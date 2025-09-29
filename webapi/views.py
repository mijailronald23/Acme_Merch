import logging

from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from rest_framework import viewsets, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiParameter, inline_serializer
)

from acme.infrastructure.django_impl.repositories import DjangoUnitOfWork
from acme.application.services.product_service import ProductService
from acme.application.services.order_service import OrderService
from acme.application.dtos import CreateProductDTO, OrderLineDTO
from acme.domain.errors import DomainError

from .serializers import (
    ProductCreateUpdateSerializer, ProductOutSerializer,
    OrderLineInSerializer, OrderOutSerializer
)

logger = logging.getLogger("webapi")

# ---------- Mini HTML Forms (para demo) ----------
def product_form_view(request):
    return render(request, "webapi/product_form.html")

def order_form_view(request):
    return render(request, "webapi/order_form.html")


# ---------- Products API ----------
@extend_schema_view(
    list=extend_schema(
        operation_id="products_list",
        responses=ProductOutSerializer(many=True)
    ),
    retrieve=extend_schema(
        operation_id="products_retrieve",
        parameters=[OpenApiParameter(name="pk", type=int, location=OpenApiParameter.PATH)],
        responses=ProductOutSerializer
    ),
    create=extend_schema(
        operation_id="products_create",
        request=ProductCreateUpdateSerializer,
        responses={201: ProductOutSerializer, 400: dict}
    ),
    update=extend_schema(
        operation_id="products_update",
        parameters=[OpenApiParameter(name="pk", type=int, location=OpenApiParameter.PATH)],
        request=ProductCreateUpdateSerializer,
        responses=ProductOutSerializer
    ),
)
class ProductViewSet(viewsets.ViewSet):
    serializer_class = ProductOutSerializer  # dica para gerador

    def list(self, request):
        svc = ProductService(DjangoUnitOfWork())
        products = svc.list()
        data = [ProductOutSerializer(p.__dict__).data for p in products]
        return Response(data)

    def retrieve(self, request, pk=None):
        svc = ProductService(DjangoUnitOfWork())
        p = svc.uow.products.get_by_id(int(pk))
        if not p:
            return Response({"detail": "Not found."}, status=404)
        return Response(ProductOutSerializer(p.__dict__).data)

    def create(self, request):
        ser = ProductCreateUpdateSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)
        svc = ProductService(DjangoUnitOfWork())
        try:
            p = svc.create(CreateProductDTO(**ser.validated_data))
            return Response(ProductOutSerializer(p.__dict__).data, status=201)
        except DomainError as e:
            return Response({"detail": str(e)}, status=400)

    def update(self, request, pk=None):
        ser = ProductCreateUpdateSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)
        svc = ProductService(DjangoUnitOfWork())
        try:
            p = svc.update(int(pk), CreateProductDTO(**ser.validated_data))
            return Response(ProductOutSerializer(p.__dict__).data)
        except DomainError as e:
            return Response({"detail": str(e)}, status=400)


# ---------- Orders API (dividida em duas views) ----------

# request body do POST /api/orders/
OrderCreateSerializer = inline_serializer(
    name="OrderCreate",
    fields={"items": OrderLineInSerializer(many=True)}
)

# item de listagem (cada linha da lista)
OrderListItemSerializer = inline_serializer(
    name="OrderListItem",
    fields={
        "id": drf_serializers.IntegerField(),
        "items_count": drf_serializers.IntegerField(),
        "total": drf_serializers.DecimalField(max_digits=12, decimal_places=2),
    }
)

# resposta de listagem (lista de itens) — já com many=True
OrderListSerializer = inline_serializer(
    name="OrderList",
    fields={
        "id": drf_serializers.IntegerField(),
        "items_count": drf_serializers.IntegerField(),
        "total": drf_serializers.DecimalField(max_digits=12, decimal_places=2),
    },
    many=True
)

@method_decorator(never_cache, name="dispatch")
class OrderListView(APIView):
    @extend_schema(
        operation_id="orders_list",
        responses=OrderListSerializer
    )
    def get(self, request):
        svc = OrderService(DjangoUnitOfWork())
        orders = svc.list_orders()
        data = [{"id": o.id, "items_count": len(o.items), "total": o.total} for o in orders]
        resp = Response(data)
        resp["Cache-Control"] = "no-store"
        return resp

    @extend_schema(
        operation_id="orders_create",
        request=OrderCreateSerializer,
        responses={201: OrderOutSerializer, 400: dict}
    )
    def post(self, request):
        items = request.data.get("items", None)
        if items is None or not isinstance(items, list) or len(items) == 0:
            return Response(
                {"detail": "Body must be {'items': [{'product_id': int, 'quantity': int}, ...]}"},
                status=400,
            )

        lines_ser = OrderLineInSerializer(data=items, many=True)
        if not lines_ser.is_valid():
            logger.warning("order_validation_errors: %s", lines_ser.errors)
            return Response({"detail": "Invalid items", "errors": lines_ser.errors}, status=400)

        lines = [OrderLineDTO(**d) for d in lines_ser.validated_data]
        svc = OrderService(DjangoUnitOfWork())
        try:
            order = svc.place_order(lines)
            payload = {
                "id": order.id,
                "items": [{
                    "product_id": i.product_id,
                    "sku": i.sku,
                    "name": i.name,
                    "unit_price": i.unit_price,
                    "quantity": i.quantity,
                    "line_total": i.line_total,
                } for i in order.items],
                "total": order.total
            }
            logger.info("order_created id=%s total=%s items=%s",
                        order.id, order.total, len(order.items))
            resp = Response(OrderOutSerializer(payload).data, status=201)
            resp["Cache-Control"] = "no-store"
            return resp

        except DomainError as e:
            return Response({"detail": str(e)}, status=400)

        except Exception as e:
            logger.exception("order_create_unexpected")
            # TEMP: expose error so we see it in Swagger/form
            return Response({"detail": "unexpected_error", "error": str(e)}, status=500)


class OrderDetailView(APIView):
    @extend_schema(
        operation_id="orders_retrieve",
        parameters=[OpenApiParameter(name="order_id", type=int, location=OpenApiParameter.PATH)],
        responses={200: OrderOutSerializer, 404: dict}
    )
    def get(self, request, order_id: int):
        svc = OrderService(DjangoUnitOfWork())
        try:
            order = svc.get_order(order_id)
            payload = {
                "id": order.id,
                "items": [{
                    "product_id": i.product_id,
                    "sku": i.sku,
                    "name": i.name,
                    "unit_price": i.unit_price,
                    "quantity": i.quantity,
                    "line_total": i.line_total,
                } for i in order.items],
                "total": order.total
            }
            return Response(OrderOutSerializer(payload).data)

        except DomainError as e:
            return Response({"detail": str(e)}, status=404)

        except Exception as e:
            logger.exception("order_detail_unexpected")
            return Response({"detail": "unexpected_error", "error": str(e)}, status=500)