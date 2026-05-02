import uuid
from datetime import datetime
from mongoengine import (
    Document,
    StringField,
    FloatField,
    IntField,
    UUIDField,
    DateTimeField,
    DictField,
    ListField,
    ReferenceField,
)


class Catalog(Document):
    """Catálogo que agrupa productos (MongoDB)."""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    name = StringField(required=True, unique=True)
    description = StringField(default="")
    created_at = DateTimeField()

    meta = {"collection": "catalogs"}

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Catalog({self.name})"


class Product(Document):
    """Producto del inventario almacenado en MongoDB."""

    STATUS_CHOICES = ("active", "inactive", "out_of_stock", "discontinued")

    id = UUIDField(primary_key=True, default=uuid.uuid4)

    # Identificadores
    odoo_id = IntField(unique=True, sparse=True)  # ID original en Odoo
    sku = StringField(unique=True, required=True)  # default_code en Odoo

    # Datos core (mapeados con Odoo)
    name = StringField(required=True)  # name en Odoo
    price = FloatField(default=0.0)  # list_price en Odoo
    stock = IntField(default=0)  # qty_available en Odoo
    description = StringField(default="")  # description_sale en Odoo

    # Campos adicionales
    image = StringField(default="")  # URL o path de imagen
    status = StringField(
        default="active"
    )  # active | inactive | out_of_stock | discontinued

    # Relación con catálogo
    catalog = ReferenceField(Catalog, null=True)

    # Enriquecimiento dinámico (no se sobreescribe al sincronizar stock de Odoo)
    attributes = DictField()  # Specs técnicas (RAM, CPU, etc.)
    metadata = DictField()  # Tags, categorías locales
    images = ListField(StringField())  # Galería de imágenes
    specifications = DictField()  # Specs adicionales de marketing

    # Auditoría
    created_at = DateTimeField()  # create_date en Odoo
    updated_at = DateTimeField()  # write_date en Odoo

    meta = {"collection": "products"}

    def save(self, *args, **kwargs):
        now = datetime.utcnow()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Product({self.sku})"
