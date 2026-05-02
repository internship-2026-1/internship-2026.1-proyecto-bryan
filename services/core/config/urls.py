from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from inventory.views import (
    CatalogListCreateView,
    HealthCheckView,
    InternalSyncProductView,
    OdooIntegrateProductsView,
    ProductDetailView,
    ProductEnrichView,
    ProductListView,
)
from sales.views import OrderDetailView, OrderListCreateView, OrderPayView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # Health
    path("api/v1/health/", HealthCheckView.as_view(), name="health-check"),
    # ── Inventory: Catalogs (MongoDB) ─────────────────────────────────────
    path(
        "api/v1/inventory/catalogs/",
        CatalogListCreateView.as_view(),
        name="catalog-list",
    ),
    # ── Inventory: Products (MongoDB) ─────────────────────────────────────
    path("api/v1/inventory/products/", ProductListView.as_view(), name="product-list"),
    path(
        "api/v1/inventory/products/<str:pk>/",
        ProductDetailView.as_view(),
        name="product-detail",
    ),
    path(
        "api/v1/inventory/products/<str:sku>/enrich/",
        ProductEnrichView.as_view(),
        name="product-enrich",
    ),
    # ── Odoo Integration ──────────────────────────────────────────────────
    path(
        "api/v1/integrate/products/",
        OdooIntegrateProductsView.as_view(),
        name="odoo-integrate",
    ),
    path(
        "internal/sync-product/",
        InternalSyncProductView.as_view(),
        name="internal-sync",
    ),
    # ── Sales: Orders (PostgreSQL) ────────────────────────────────────────
    path("api/v1/orders/", OrderListCreateView.as_view(), name="order-list"),
    path(
        "api/v1/orders/<uuid:order_id>/", OrderDetailView.as_view(), name="order-detail"
    ),
    path(
        "api/v1/orders/<uuid:order_id>/pay/", OrderPayView.as_view(), name="order-pay"
    ),
]
