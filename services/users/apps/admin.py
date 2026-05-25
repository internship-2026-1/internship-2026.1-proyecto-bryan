from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # Configuración para que el admin use username como USERNAME_FIELD
    # En lugar de email (que era el USERNAME_FIELD original)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
    )
    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = ("is_staff", "is_active", "is_superuser")

    # Campo de búsqueda para autenticación en admin
    # Django admin usa estos campos para las búsquedas de usuarios
    ordering = ("-date_joined",)
