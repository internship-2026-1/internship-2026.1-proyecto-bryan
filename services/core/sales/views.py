from decimal import Decimal

from mongoengine.errors import DoesNotExist
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.models import Product
from .models import IntegrationLog, Order, OrderItem
from .serializers import OrderCreateSerializer, OrderSerializer


def _serialize_order(order):
    items = [
        {
            "id": item.id,
            "product_sku": item.product_sku,
            "quantity": item.quantity,
            "price_at_purchase": str(item.price_at_purchase),
        }
        for item in order.items.all()
    ]
    return {
        "id": order.id,
        "customer_id": str(order.customer_id) if order.customer_id else None,
        "items": items,
        "total_price": str(order.total_price),
        "status": order.status,
        "odoo_sale_order_id": order.odoo_sale_order_id,
        "created_at": order.created_at.isoformat(),
    }


class OrderListCreateView(APIView):
    """
    GET  /api/v1/orders/  — lista todas las órdenes.
    POST /api/v1/orders/  — crea una orden verificando stock en MongoDB.
    """

    def get(self, request):
        orders = Order.objects.prefetch_related("items").all()
        return Response([_serialize_order(o) for o in orders])

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        items_data = serializer.validated_data["items"]

        # --- Validar stock en MongoDB antes de crear nada ---
        products_found = {}
        for item in items_data:
            sku = item["product_sku"]
            qty = item["quantity"]
            try:
                product = Product.objects.get(sku=sku)
            except DoesNotExist:
                return Response(
                    {"error": f"Producto '{sku}' no encontrado en el inventario."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if product.stock < qty:
                return Response(
                    {"error": "stock insuficiente"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            products_found[sku] = product

        # --- Crear Orden ---
        total = Decimal("0.00")
        order = Order.objects.create(status="pending", total_price=Decimal("0.00"))

        for item in items_data:
            sku = item["product_sku"]
            qty = item["quantity"]
            product = products_found[sku]
            price = Decimal(str(product.price))
            OrderItem.objects.create(
                order=order,
                product_sku=sku,
                quantity=qty,
                price_at_purchase=price,
            )
            total += price * qty

        order.total_price = total
        order.save()

        return Response(_serialize_order(order), status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    """GET /api/v1/orders/{order_id}/"""

    def get(self, request, order_id):
        try:
            order = Order.objects.prefetch_related("items").get(pk=order_id)
        except Order.DoesNotExist:
            return Response(
                {"error": "Orden no encontrada."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(_serialize_order(order))


class OrderPayView(APIView):
    """
    POST /api/v1/orders/{order_id}/pay/
    Simula el pago y dispara la tarea Celery para sincronizar con Odoo.
    """

    def post(self, request, order_id):
        try:
            order = Order.objects.prefetch_related("items").get(pk=order_id)
        except Order.DoesNotExist:
            return Response(
                {"error": "Orden no encontrada."}, status=status.HTTP_404_NOT_FOUND
            )

        if order.status == "paid":
            return Response(
                {"error": "Este pedido ya fue confirmado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = "paid"
        order.save()

        # Registrar log inicial
        IntegrationLog.objects.create(
            order=order,
            status_code="queued",
            raw_response="Tarea enviada a Celery para sincronizar con Odoo.",
        )

        # Disparar tarea asíncrona hacia Odoo
        from .tasks import sync_order_to_odoo

        sync_order_to_odoo.delay(order.id)

        return Response(
            {
                "message": "Pago simulado exitosamente. El stock en Odoo será actualizado en breve.",
                "order": _serialize_order(order),
            },
            status=status.HTTP_200_OK,
        )
