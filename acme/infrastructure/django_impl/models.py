from django.db import models

class ProductModel(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class OrderModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItemModel(models.Model):
    order = models.ForeignKey(OrderModel, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(ProductModel, on_delete=models.PROTECT)
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()