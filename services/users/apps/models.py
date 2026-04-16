from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.db import models
import uuid  # req1: Importar UUID para IDs de usuarios
import secrets  # (reset) Para generar tokens seguros
from django.utils import timezone  # (reset) Para manejar expiración de tokens
from datetime import timedelta  # (reset) Para calcular tiempo de expiración


class UserManager(BaseUserManager):
    """
    Manager personalizado para crear usuarios con username y email.
    Se agregó validación de username en create_user y create_superuser
    BaseUseManager (proporciona métodos para crear usuarios y superusuarios)
        - create_user(): Crea un usuario normal con username, email y password
        - create_superuser(): Crea un superusuario con permisos de administrador
    """

    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError("El nombre de usuario es obligatorio")
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)  # Aqui hasheamos el password
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de Usuario personalizado para la plataforma.
    Se reemplazó el modelo por defecto de Django para mayor flexibilidad.
    Heredados de AbstractBaseUser:
        password,
        last_login,
        is_active,
        is_staff,
        date_joined (agregado manualmente) y permisos.

    Mixin: agrega campos y métodos para manejo de permisos
        (is_superuser, groups, user_permissions)
    """

    # req1: Cambiar ID por defecto a UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone = models.CharField(max_length=20, blank=True)
    # Control de estado del usuario
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    # MODIF: date_joined automático para auditoría - se retorna como created_at en serializer
    date_joined = models.DateTimeField(auto_now_add=True)
    # req2: Rol del usuario con valor por defecto 'b2c' (Business to Consumer)
    ROLE_CHOICES = [
        ("b2c", "Business to Consumer"),
        ("b2b", "Business to Business"),
        ("admin", "Administrator"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="b2c")
    # Campos opcionales de perfil
    address = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=50, blank=True)
    objects = UserManager()

    # MODIF: USERNAME_FIELD cambiado de "email" a "username" para autenticación
    USERNAME_FIELD = "username"
    # MODIF: REQUIRED_FIELDS actualizado para create_superuser
    REQUIRED_FIELDS = ["email", "first_name", "last_name"]

    def __str__(self):
        return self.email


# (reset) Modelo para almacenar tokens de restablecimiento de contraseña
class PasswordResetToken(models.Model):  # (reset)
    """
    # (reset) Almacena tokens temporales para reset de contraseña.
    # (reset) Cada token tiene expiración de 1 hora y uso único.
    """

    user = models.ForeignKey(  # (reset)
        User, on_delete=models.CASCADE, related_name="password_reset_tokens"  # (reset)
    )
    token = models.CharField(max_length=128, unique=True)  # (reset) Hash único
    created_at = models.DateTimeField(auto_now_add=True)  # (reset)
    expires_at = models.DateTimeField()  # (reset) Fecha de expiración
    used = models.BooleanField(default=False)  # (reset) Si ya fue utilizado

    def save(self, *args, **kwargs):  # (reset)
        """# (reset) Genera token y fecha de expiración automáticamente."""
        if not self.token:  # (reset)
            self.token = secrets.token_urlsafe(
                48
            )  # (reset) Token seguro de 64 chars aprox
        if not self.expires_at:  # (reset)
            self.expires_at = timezone.now() + timedelta(
                hours=1
            )  # (reset) Expira en 1 hora
        super().save(*args, **kwargs)  # (reset)

    def is_valid(self):  # (reset)
        """# (reset) Verifica si el token no ha expirado y no fue usado."""
        return not self.used and timezone.now() < self.expires_at  # (reset)

    def __str__(self):  # (reset)
        return f"Reset token for {self.user.email} - {'valid' if self.is_valid() else 'expired/used'}"  # (reset)
