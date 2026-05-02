import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sales", "0001_initial"),
    ]

    operations = [
        # Eliminar modelos anteriores
        migrations.DeleteModel(name="Transaction"),
        migrations.DeleteModel(name="Order"),
        # Recrear Order con nueva estructura
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "customer_id",
                    models.UUIDField(blank=True, default=uuid.uuid4, null=True),
                ),
                (
                    "total_price",
                    models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("paid", "Paid"),
                            ("cancelled", "Cancelled"),
                            ("synced", "Synced"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("odoo_sale_order_id", models.IntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        # OrderItem
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("product_sku", models.CharField(max_length=100)),
                ("quantity", models.IntegerField()),
                (
                    "price_at_purchase",
                    models.DecimalField(decimal_places=2, max_digits=12),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="sales.order",
                    ),
                ),
            ],
        ),
        # IntegrationLog
        migrations.CreateModel(
            name="IntegrationLog",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("status_code", models.CharField(max_length=20)),
                ("raw_response", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "order",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="logs",
                        to="sales.order",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
