from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re
from .models import User
from django.contrib.auth import authenticate  # (login) Para autenticar credenciales
from rest_framework_simplejwt.tokens import RefreshToken  # (login) Para generar JWT


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro de usuarios con validaciones completas.
    Incluye: validación de contraseña, email único, username único, teléfono válido.
    req2: Ahora incluye el campo 'role' con valor por defecto 'b2c'
    """

    # Campo write_only para que la contraseña no se retorne en respuesta;
    password = serializers.CharField(write_only=True, required=True)
    phone = serializers.CharField(required=True, allow_blank=False)
    created_at = serializers.SerializerMethodField()
    # req2: Agregar campo role con valores permitidos, default 'b2c' si no se envía
    role = serializers.ChoiceField(
        choices=["b2c", "b2b", "admin"], required=False, default="b2c"
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone",
            "role",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {
            "username": {"required": True},
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def get_created_at(self, obj):
        return obj.date_joined.isoformat()

    def validate_username(self, value):
        """
        - Longitud: 3-30 caracteres (requisito)
        - Unicidad: Verifica que no exista en la BD
        """
        if len(value) < 3 or len(value) > 30:
            raise serializers.ValidationError(
                "El nombre de usuario debe tener entre 3 y 30 caracteres."
            )

        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Este nombre de usuario ya está registrado."
            )

        return value

    def validate_email(self, value):
        """
        Validación de email
        - Formato: Validado automáticamente por EmailField
        - Unicidad: Verifica que no exista en la BD
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Este correo electrónico ya está registrado."
            )

        return value

    def validate_phone(self, value):
        """
        Validación de teléfono.
        - Patrón: +?[1-9]\d{8,14} (9-15 dígitos, puede tener +)
        - Acepta formatos: +573001112233, +57 300 1112233, 573001112233
        - Rechaza: números muy cortos (123), formatos inválidos
        """
        phone_pattern = r"^\+?[1-9]\d{8,14}$"
        clean_phone = re.sub(r"[\s\-]", "", value)

        if not re.match(phone_pattern, clean_phone):
            raise serializers.ValidationError(
                "El formato del teléfono no es válido. Ejemplo: +573001112233"
            )

        return value

    def validate_password(self, value):
        """
        Validación de contraseña con política de seguridad fuerte
        - Mínimo: 8 caracteres
        - Complejidad: Mayúscula + Número + Carácter especial
        - Validación Django: Contraseña contra diccionarios comunes
        """
        try:
            validate_password(value)  # Validación estándar de Django
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

        # Validaciones adicionales personalizadas
        if len(value) < 8:
            raise serializers.ValidationError(
                "La contraseña debe tener al menos 8 caracteres."
            )

        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos una mayúscula."
            )

        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos un número."
            )

        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos un carácter especial."
            )

        return value

    def create(self, validated_data):
        """
        Crea el usuario con contraseña hasheada
        - Extrae password del validated_data
        - Usa UserManager.create_user que hashea la contraseña con PBKDF2
        - NO se retorna la contraseña en la respuesta (write_only=True)
        - Usuario creado con is_active=True (sin verificación por email)
        req2: Asigna rol al usuario (por defecto 'b2c' si no se proporciona)
        """
        password = validated_data.pop("password")
        # req2: Usar el rol del usuario (default 'b2c' si no se proporciona)
        role = validated_data.get("role", "b2c")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=password,  # Se hashea en UserManager.create_user
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            phone=validated_data.get("phone", ""),
            role=role,  # req2: Asignar role al usuario
            is_active=True,  # MODIF: Usuario activo por defecto (sin verificación)
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    # (login) Serializer para autenticación de usuarios
    # (login) Valida credenciales y genera tokens JWT (access + refresh)
    # (login) Retorna: {"access": "token", "refresh": "token"}
    """

    # (login) Campo username para identificar usuario
    username = serializers.CharField(required=True)
    # (login) Campo password para validar credenciales
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        """
        # (login) Valida credenciales contra la base de datos
        # (login) Retorna 401 si no son válidas
        """
        username = data.get("username")
        password = data.get("password")

        # (login) Autentica usando Django authenticate
        user = authenticate(username=username, password=password)

        if not user:
            # (login) Credenciales inválidas - retorna error 401
            raise serializers.ValidationError(
                "Credenciales inválidas. Verifica el usuario o contraseña."
            )

        # (login) Genera tokens JWT (access y refresh)
        refresh = RefreshToken.for_user(user)
        data["access"] = str(refresh.access_token)  # (login) Token de acceso
        data["refresh"] = str(refresh)  # (login) Token de refresh
        data["user"] = user

        return data


# (update) Serializer para actualización parcial del perfil de usuario
class UserProfileUpdateSerializer(serializers.ModelSerializer):  # (update)
    """
    # (update) Serializer para actualizar perfil de usuario autenticado.
    # (update) email y username son de solo lectura por seguridad.
    # (update) Permite actualizar: first_name, last_name, phone, address, country.
    """

    created_at = serializers.SerializerMethodField()  # (update)

    class Meta:  # (update)
        model = User  # (update)
        fields = [  # (update)
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
            "address",
            "country",
            "created_at",
        ]
        read_only_fields = [  # (update) Campos que no se pueden modificar
            "id",
            "username",
            "email",
            "role",
            "created_at",
        ]

    def get_created_at(self, obj):  # (update)
        return obj.date_joined.isoformat()  # (update)


# (reset) Serializer para solicitar restablecimiento de contraseña
class PasswordResetRequestSerializer(serializers.Serializer):  # (reset)
    """# (reset) Valida el email para solicitar reset de contraseña."""

    email = serializers.EmailField(required=True)  # (reset)


# (reset) Serializer para confirmar el cambio de contraseña con token
class PasswordResetConfirmSerializer(serializers.Serializer):  # (reset)
    """# (reset) Valida el token y la nueva contraseña."""

    token = serializers.CharField(required=True)  # (reset)
    new_password = serializers.CharField(required=True, write_only=True)  # (reset)

    def validate_new_password(self, value):  # (reset)
        """# (reset) Aplica las mismas reglas de contraseña que el registro."""
        try:  # (reset)
            validate_password(value)  # (reset)
        except ValidationError as e:  # (reset)
            raise serializers.ValidationError(str(e))  # (reset)

        if len(value) < 8:  # (reset)
            raise serializers.ValidationError(  # (reset)
                "La contraseña debe tener al menos 8 caracteres."  # (reset)
            )
        if not any(char.isupper() for char in value):  # (reset)
            raise serializers.ValidationError(  # (reset)
                "La contraseña debe contener al menos una mayúscula."  # (reset)
            )
        if not any(char.isdigit() for char in value):  # (reset)
            raise serializers.ValidationError(  # (reset)
                "La contraseña debe contener al menos un número."  # (reset)
            )
        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in value):  # (reset)
            raise serializers.ValidationError(  # (reset)
                "La contraseña debe contener al menos un carácter especial."  # (reset)
            )
        return value  # (reset)
