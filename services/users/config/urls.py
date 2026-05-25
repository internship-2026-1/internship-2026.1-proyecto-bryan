from django.contrib import admin
from django.urls import path
from apps.views import (
    UserRegisterView,
    HelloWorldView,
    UserLoginView,
    UserProfileUpdateView,  # Importa vista de actualización de perfil
    PasswordResetRequestView,  # Importa vista de solicitud de reset
    PasswordResetConfirmView,  # Importa vista de confirmación de reset
    UserListView,
)  # Importa LoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("hello/", HelloWorldView.as_view(), name="hello-world"),
    path("register/", UserRegisterView.as_view(), name="user-register"),
    path("auth/login/", UserLoginView.as_view(), name="user-login"),
    path(
        "profile/update/", UserProfileUpdateView.as_view(), name="user-profile-update"
    ),
    path(
        "auth/password-reset/",   
        PasswordResetRequestView.as_view(),  
        name="password-reset-request",  
    ),
    path(
        "auth/password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("users/", UserListView.as_view(), name="user-list"),
]
