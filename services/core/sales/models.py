import uuid
from django.db import models


class Order(models.Model):
    """Orden de compra — almacenada en PostgreSQL."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
        ("synced", "Synced"),  # Confirmado en Odoo vía Celery
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.UUIDField(null=True, blank=True, default=uuid.uuid4)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    odoo_sale_order_id = models.IntegerField(
        null=True, blank=True
    )  # ID de la SO en Odoo
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"


class OrderItem(models.Model):
    """Línea de producto dentro de una orden."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_sku = models.CharField(max_length=100)
    quantity = models.IntegerField()
    price_at_purchase = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"OrderItem {self.product_sku} x{self.quantity}"


class IntegrationLog(models.Model):
    """Log de trazabilidad de cada llamada hacia Odoo."""

    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
    )
    status_code = models.CharField(max_length=20)
    raw_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"IntegrationLog order={self.order_id} status={self.status_code}"
