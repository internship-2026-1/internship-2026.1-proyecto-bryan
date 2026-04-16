from django.contrib import admin
from django.urls import path
from apps.views import (
    UserRegisterView,
    HelloWorldView,
    UserLoginView,
    UserProfileUpdateView,  # (update) Importa vista de actualización de perfil
    PasswordResetRequestView,  # (reset) Importa vista de solicitud de reset
    PasswordResetConfirmView,  # (reset) Importa vista de confirmación de reset
)  # (login) Importa LoginView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("hello/", HelloWorldView.as_view(), name="hello-world"),
    path("register/", UserRegisterView.as_view(), name="user-register"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path(
        "gateway-docs/",
        SpectacularSwaggerView.as_view(url="/user/api/v1/schema/"),
        name="gateway-swagger-ui",
    ),
    path("auth/login/", UserLoginView.as_view(), name="user-login"),
    path(
        "profile/update/", UserProfileUpdateView.as_view(), name="user-profile-update"
    ),
    path(
        "auth/password-reset/",  # (reset)
        PasswordResetRequestView.as_view(),  # (reset)
        name="password-reset-request",  # (reset)
    ),
    path(
        "auth/password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
]
