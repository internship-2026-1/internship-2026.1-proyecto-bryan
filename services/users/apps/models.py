from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.db import models
import uuid  
import secrets  
from django.utils import timezone  
from datetime import timedelta  


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

    # Cambiar ID por defecto a UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone = models.CharField(max_length=20, blank=True)
    # Control de estado del usuario
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    # date_joined automático para auditoría - se retorna como created_at en serializer
    date_joined = models.DateTimeField(auto_now_add=True)
    # Rol del usuario con valor por defecto 'b2c' (Business to Consumer)
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

    # USERNAME_FIELD cambiado de "email" a "username" para autenticación
    USERNAME_FIELD = "username"
    # REQUIRED_FIELDS actualizado para create_superuser
    REQUIRED_FIELDS = ["email", "first_name", "last_name"]

    def __str__(self):
        return self.email


# Modelo para almacenar tokens de restablecimiento de contraseña
class PasswordResetToken(models.Model):  
    """
    # Almacena tokens temporales para reset de contraseña.
    # Cada token tiene expiración de 1 hora y uso único.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="password_reset_tokens"
    )
    token = models.CharField(max_length=128, unique=True)  # Hash único
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # Fecha de expiración
    used = models.BooleanField(default=False)  # Si ya fue utilizado

    def save(self, *args, **kwargs):  # 
        """Genera token y fecha de expiración automáticamente."""
        if not self.token:  
            self.token = secrets.token_urlsafe(
                48
            )  # Token seguro de 64 chars aprox
        if not self.expires_at:  
            self.expires_at = timezone.now() + timedelta(
                hours=1
            )  # Expira en 1 hora
        super().save(*args, **kwargs)

    def is_valid(self):
        """Verifica si el token no ha expirado y no fue usado."""
        return not self.used and timezone.now() < self.expires_at

    def __str__(self):
        return f"Reset token for {self.user.email} - {'valid' if self.is_valid() else 'expired/used'}"
