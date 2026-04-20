from django.contrib import admin
from django.urls import path, include
from api.views import HealthCheckView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # (c) Admin y documentación
    path("admin/", admin.site.urls),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # (c) API v1 - Health check
    path("api/v1/health/", HealthCheckView.as_view(), name="health-check"),
]
