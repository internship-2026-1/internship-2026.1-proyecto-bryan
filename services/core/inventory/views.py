import xmlrpc.client

from django.conf import settings
from mongoengine.errors import DoesNotExist, NotUniqueError, ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Catalog, Product
from .serializers import (
    CatalogSerializer,
    EnrichProductSerializer,
    ProductAssignCatalogSerializer,
    ProductSerializer,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialize_catalog(c):
    return {
        "id": str(c.id),
        "name": c.name,
        "description": c.description or "",
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _serialize_product(p):
    catalog_name = None
    try:
        if p.catalog:
            catalog_name = p.catalog.name
    except Exception:
        # El catálogo referenciado fue eliminado — limpiar la referencia huérfana
        p.catalog = None
        p.save()
        catalog_name = None

    return {
        "id": str(p.id),
        "catalog": catalog_name,
        "name": p.name,
        "sku": p.sku,
        "price": str(round(p.price, 2)) if p.price is not None else "0.00",
        "stock": p.stock,
        "description": p.description or "",
        "image": p.image or "",
        "status": p.status or "active",
        "odoo_id": p.odoo_id,
        "attributes": p.attributes or {},
        "metadata": p.metadata or {},
        "images": p.images or [],
        "specifications": p.specifications or {},
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


def _odoo_connect():
    """Abre sesión XML-RPC con Odoo y devuelve (models_proxy, uid)."""
    url = settings.ODOO_URL
    db = settings.ODOO_DB
    user = settings.ODOO_USER
    password = settings.ODOO_PASSWORD

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, user, password, {})
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    return models, uid, db, password


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class HealthCheckView(APIView):
    def get(self, request):
        return Response({"service": "core", "status": "ok"}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Catalogs  —  POST /api/v1/inventory/catalogs/
# ---------------------------------------------------------------------------


class CatalogListCreateView(APIView):
    """GET /api/v1/inventory/catalogs/  |  POST /api/v1/inventory/catalogs/"""

    def get(self, request):
        catalogs = Catalog.objects.all()
        return Response([_serialize_catalog(c) for c in catalogs])

    def post(self, request):
        serializer = CatalogSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            catalog = Catalog(
                name=serializer.validated_data["name"],
                description=serializer.validated_data.get("description", ""),
            )
            catalog.save()
            return Response(_serialize_catalog(catalog), status=status.HTTP_201_CREATED)
        except NotUniqueError:
            return Response(
                {"error": "Ya existe un catálogo con ese nombre."},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ---------------------------------------------------------------------------
# Products list  —  GET /api/v1/inventory/products/
# ---------------------------------------------------------------------------


class ProductListView(APIView):
    """GET /api/v1/inventory/products/"""

    def get(self, request):
        products = Product.objects.all()
        return Response([_serialize_product(p) for p in products])


# ---------------------------------------------------------------------------
# Product detail/update  —  PUT /api/v1/inventory/products/{product_id}/
# ---------------------------------------------------------------------------


class ProductDetailView(APIView):
    """GET /api/v1/inventory/products/{pk}/  |  PUT (asignar catálogo/estado)"""

    def _get_product(self, pk):
        try:
            return Product.objects.get(id=pk)
        except (DoesNotExist, ValidationError):
            return None

    def get(self, request, pk):
        product = self._get_product(pk)
        if not product:
            return Response(
                {"error": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(_serialize_product(product))

    def put(self, request, pk):
        product = self._get_product(pk)
        if not product:
            return Response(
                {"error": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductAssignCatalogSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Asignar catálogo
        if "catalog" in data and data["catalog"] is not None:
            try:
                catalog = Catalog.objects.get(id=data["catalog"])
                product.catalog = catalog
            except (DoesNotExist, ValidationError):
                return Response(
                    {"error": "Catálogo no encontrado."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        elif "catalog" in data and data["catalog"] is None:
            product.catalog = None

        # Asignar status
        if "status" in data:
            product.status = data["status"]

        product.save()
        return Response(_serialize_product(product))


# ---------------------------------------------------------------------------
# Enrich  —  PATCH /api/v1/inventory/products/{sku}/enrich/
# ---------------------------------------------------------------------------


class ProductEnrichView(APIView):
    """PATCH /api/v1/inventory/products/{sku}/enrich/ — enriquecimiento de marketing."""

    def patch(self, request, sku):
        try:
            product = Product.objects.get(sku=sku)
        except (DoesNotExist, ValidationError):
            return Response(
                {"error": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EnrichProductSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        # Solo actualizamos campos de enriquecimiento — NO price/stock (esos los maneja Odoo)
        if "description" in data:
            product.description = data["description"]
        if "image" in data:
            product.image = data["image"]
        if "images" in data:
            product.images = data["images"]
        if "specifications" in data:
            product.specifications = data["specifications"]

        product.save()
        return Response(_serialize_product(product))


# ---------------------------------------------------------------------------
# Odoo Integration  —  POST /api/v1/integrate/products/
# ---------------------------------------------------------------------------


class OdooIntegrateProductsView(APIView):
    """
    POST /api/v1/integrate/products/
    Trae productos de Odoo.  Si el SKU no existe → crea.  Si existe → actualiza solo el stock.
    """

    def post(self, request):
        try:
            models_proxy, uid, db, password = _odoo_connect()
        except Exception as e:
            return Response(
                {"error": f"No se pudo conectar a Odoo: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Traer productos activos de Odoo
        try:
            odoo_fields = [
                "id",
                "default_code",
                "name",
                "list_price",
                "qty_available",
                "description_sale",
                "image_1920",
            ]
            odoo_products = models_proxy.execute_kw(
                db,
                uid,
                password,
                "product.template",
                "search_read",
                [[["active", "=", True], ["default_code", "!=", False]]],
                {"fields": odoo_fields, "limit": 200},
            )
        except Exception as e:
            return Response(
                {"error": f"Error al consultar productos en Odoo: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        created = 0
        updated = 0

        for op in odoo_products:
            sku = op.get("default_code") or ""
            if not sku:
                continue

            odoo_stock = int(op.get("qty_available") or 0)

            try:
                # Producto ya existe → actualizar SOLO el stock
                product = Product.objects.get(sku=sku)
                product.stock = odoo_stock
                product.save()
                updated += 1
            except DoesNotExist:
                # Producto nuevo → crear con todos los campos
                product = Product(
                    odoo_id=op["id"],
                    sku=sku,
                    name=op.get("name", ""),
                    price=float(op.get("list_price") or 0.0),
                    stock=odoo_stock,
                    description=op.get("description_sale") or "",
                    image=op.get("image_1920") or "",
                    status="active",
                )
                product.save()
                created += 1

        total = created + updated
        return Response(
            {
                "message": "Integracion completada",
                "created": created,
                "updated": updated,
                "total": total,
            },
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Internal sync (reqB)  —  PATCH /internal/sync-product/
# ---------------------------------------------------------------------------


class InternalSyncProductView(APIView):
    """
    PATCH /internal/sync-product/
    Upsert desde Odoo: odoo_id, sku, price, stock.
    NO sobreescribe description, images, specifications.
    """

    def patch(self, request):
        odoo_id = request.data.get("odoo_id")
        sku = request.data.get("sku")
        price = request.data.get("price")
        stock = request.data.get("stock")

        if not sku:
            return Response(
                {"error": "El campo 'sku' es requerido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            product = Product.objects.get(sku=sku)
            # Actualiza solo los campos de Odoo — respeta enriquecimiento manual
            if stock is not None:
                product.stock = int(stock)
            if price is not None:
                product.price = float(price)
            if odoo_id is not None:
                product.odoo_id = int(odoo_id)
            product.save()
            created = False
        except DoesNotExist:
            name = request.data.get("name", sku)
            product = Product(
                odoo_id=odoo_id,
                sku=sku,
                name=name,
                price=float(price or 0),
                stock=int(stock or 0),
                status="active",
            )
            product.save()
            created = True

        return Response(
            {
                "action": "created" if created else "updated",
                "product": _serialize_product(product),
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
