import xmlrpc.client

from celery import shared_task
from django.conf import settings


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def sync_order_to_odoo(self, order_id):
    """
    Tarea Celery: sincroniza una orden pagada con Odoo vía XML-RPC.
    Flujo:
        1. Leer OrderItems desde PostgreSQL.
        2. Autenticar en Odoo.
        3. Crear Sale Order en Odoo con los mismos items.
        4. Actualizar Order.odoo_sale_order_id y status='synced' en PostgreSQL.
        5. Registrar el resultado en IntegrationLog.
    """
    # Importación diferida para evitar problemas de arranque con Celery
    from .models import IntegrationLog, Order

    try:
        order = Order.objects.prefetch_related("items").get(pk=order_id)
    except Order.DoesNotExist:
        # Orden no existe — no tiene sentido reintentar
        return {"error": f"Order {order_id} no encontrada."}

    raw_request = {
        "order_id": order_id,
        "items": [
            {
                "sku": item.product_sku,
                "qty": item.quantity,
                "price": str(item.price_at_purchase),
            }
            for item in order.items.all()
        ],
    }

    try:
        # --- Autenticar en Odoo ---
        url = settings.ODOO_URL
        db = settings.ODOO_DB
        user = settings.ODOO_USER
        password = settings.ODOO_PASSWORD

        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, user, password, {})
        if not uid:
            raise ConnectionError("Autenticación en Odoo fallida.")

        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

        # --- Por cada item: buscar product.product y descontar stock en Odoo ---
        synced_items = []
        for item in order.items.all():
            # Buscar el product.product por SKU (default_code)
            product_ids = models.execute_kw(
                db,
                uid,
                password,
                "product.product",
                "search",
                [[["default_code", "=", item.product_sku]]],
            )
            if not product_ids:
                raise ValueError(f"SKU '{item.product_sku}' no encontrado en Odoo.")

            product_id = product_ids[0]

            # Buscar el stock.quant en la ubicación interna (WH/Stock)
            quant_ids = models.execute_kw(
                db,
                uid,
                password,
                "stock.quant",
                "search",
                [
                    [
                        ["product_id", "=", product_id],
                        ["location_id.usage", "=", "internal"],
                    ]
                ],
            )
            if not quant_ids:
                raise ValueError(
                    f"No se encontró stock interno para SKU '{item.product_sku}' en Odoo."
                )

            # Leer cantidad actual
            quant_data = models.execute_kw(
                db,
                uid,
                password,
                "stock.quant",
                "read",
                [quant_ids],
                {"fields": ["quantity"]},
            )
            current_qty = quant_data[0]["quantity"]
            new_qty = current_qty - item.quantity

            if new_qty < 0:
                raise ValueError(
                    f"Stock insuficiente en Odoo para '{item.product_sku}': "
                    f"disponible={current_qty}, solicitado={item.quantity}."
                )

            # Escribir la nueva cantidad directamente en stock.quant
            models.execute_kw(
                db,
                uid,
                password,
                "stock.quant",
                "write",
                [quant_ids, {"quantity": new_qty}],
            )
            synced_items.append(
                {
                    "sku": item.product_sku,
                    "qty_descontada": item.quantity,
                    "stock_anterior": current_qty,
                    "stock_nuevo": new_qty,
                }
            )

        # --- Actualizar la orden en PostgreSQL ---
        order.status = "synced"
        order.save()

        raw_response = f"Stock descontado en Odoo: {synced_items}"
        IntegrationLog.objects.create(
            order=order,
            status_code="synced",
            raw_response=raw_response,
        )
        return {"status": "synced", "items": synced_items}

    except Exception as exc:
        # Registrar el fallo
        IntegrationLog.objects.create(
            order=order,
            status_code="error",
            raw_response=str(exc),
        )
        # Reintentar con back-off (hasta max_retries veces)
        raise self.retry(exc=exc)
