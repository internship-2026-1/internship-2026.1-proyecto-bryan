from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product_sku", "quantity", "price_at_purchase"]
        read_only_fields = ["id", "price_at_purchase"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_id",
            "items",
            "total_price",
            "status",
            "odoo_sale_order_id",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "customer_id",
            "total_price",
            "status",
            "odoo_sale_order_id",
            "created_at",
        ]


class OrderCreateItemSerializer(serializers.Serializer):
    """Línea de item recibida al crear una orden."""

    product_sku = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    """Body para POST /api/v1/orders/"""

    items = OrderCreateItemSerializer(many=True, min_length=1)
