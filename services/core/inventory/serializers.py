from rest_framework import serializers


class CatalogSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, default="", allow_blank=True)
    created_at = serializers.DateTimeField(read_only=True)


class ProductSerializer(serializers.Serializer):
    """Creación/actualización completa de producto."""

    id = serializers.CharField(read_only=True)
    sku = serializers.CharField(max_length=100)
    odoo_id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(max_length=300)
    price = serializers.FloatField(required=False, default=0.0)
    stock = serializers.IntegerField(required=False, default=0)
    description = serializers.CharField(required=False, default="", allow_blank=True)
    image = serializers.CharField(required=False, default="", allow_blank=True)
    status = serializers.ChoiceField(
        choices=["active", "inactive", "out_of_stock", "discontinued"],
        required=False,
        default="active",
    )
    catalog = serializers.CharField(required=False, allow_null=True)
    attributes = serializers.DictField(required=False, default=dict)
    metadata = serializers.DictField(required=False, default=dict)
    images = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    specifications = serializers.DictField(required=False, default=dict)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ProductAssignCatalogSerializer(serializers.Serializer):
    """PUT /api/v1/inventory/products/{id}/ — asignar catálogo, estado, precio y stock."""

    catalog = serializers.CharField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=["active", "inactive", "out_of_stock", "discontinued"],
        required=False,
    )
    price = serializers.FloatField(required=False)
    stock = serializers.IntegerField(required=False)


class EnrichProductSerializer(serializers.Serializer):
    """PATCH /api/v1/inventory/products/{sku}/enrich/ — enriquecimiento de marketing."""

    description = serializers.CharField(required=False, allow_blank=True)
    images = serializers.ListField(child=serializers.CharField(), required=False)
    specifications = serializers.DictField(required=False)
    image = serializers.CharField(required=False, allow_blank=True)
