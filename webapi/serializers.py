from rest_framework import serializers

class ProductCreateUpdateSerializer(serializers.Serializer):
    sku = serializers.CharField(max_length=50)
    name = serializers.CharField(max_length=200)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock = serializers.IntegerField(min_value=0)

class ProductOutSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sku = serializers.CharField()
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock = serializers.IntegerField()

class OrderLineInSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class OrderOutItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    sku = serializers.CharField()
    name = serializers.CharField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity = serializers.IntegerField()
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2)

class OrderOutSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    items = OrderOutItemSerializer(many=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
