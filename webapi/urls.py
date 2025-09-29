from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ProductViewSet,
    OrderListView, OrderDetailView,
    product_form_view, order_form_view
)

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="products")

urlpatterns = [
    path("", include(router.urls)),

    path("orders/", OrderListView.as_view()),
    path("orders/<int:order_id>/", OrderDetailView.as_view()),

    # Mini forms (demo)
    path("product-form/", product_form_view, name="product-form"),
    path("order-form/", order_form_view, name="order-form"),
]