from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserProfileUpdateSerializer,  # (update) Importa serializer de perfil
    PasswordResetRequestSerializer,  # (reset) Importa serializer de solicitud de reset
    PasswordResetConfirmSerializer,  # (reset) Importa serializer de confirmación de reset
)  # (login) Importa LoginSerializer
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)  # (update) Importa IsAuthenticated
from .models import User, PasswordResetToken  # (reset) Importa modelos
from django.core.mail import send_mail  # (reset) Para enviar correos
from django.conf import settings  # (reset) Para acceder a configuración
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema


# req2: Helper function para estructurar respuestas API estándar
def format_response(success, message, data=None, http_status=200):
    """
    req2: Formatea respuestas API con estructura estándar:
    {
        "success": true/false,
        "message": "descripción",
        "data": [...],
        "status": 200/400/500
    }
    """
    return {
        "success": success,
        "message": message,
        "data": data if data is not None else [],
        "status": http_status,
    }


class HelloWorldView(APIView):
    """
    Vista simple de prueba para verificar que el API está funcionando.
    MODIF: Agregada para validar comunicación entre nginx y Django.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"message": "Hello, world!"})


class UserRegisterView(APIView):
    """
    Endpoint para registro de usuarios (Requisito 1: Registro).
    MODIF: Actualizada para retornar datos completos del usuario en respuesta.
    Cambiado: Respuesta anterior retornaba mensaje, ahora retorna serializer.data
    """

    permission_classes = [AllowAny]  # Público - no requiere autenticación

    @extend_schema(
        request=UserRegisterSerializer,
        responses={
            201: OpenApiTypes.OBJECT,  # MODIF: Documentación para respuesta exitosa
            400: OpenApiTypes.OBJECT,  # Documentación para errores de validación
            401: OpenApiTypes.OBJECT,  # Documentación para errores de autenticación
        },
        parameters=[
            OpenApiParameter(
                name="x-api-key",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=False,
                description="API key requerida por el gateway.",
            ),
            OpenApiParameter(
                name="x-origin",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=False,
                description="Origen requerido por el gateway.",
            ),
        ],
    )
    def post(self, request):
        """
        POST /register/ - Registra un nuevo usuario
        MODIF: Cambio principal - retorna datos del usuario en lugar de mensaje

        Request:
        {
            "username": "jdoe",
            "email": "jdoe@empresa.com",
            "password": "Str0ngP@ssw0rd!",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+573001112233",
            "role": "b2c"
        }

        Response 201:
        req2: Estructura estándar de respuesta
        {
            "success": true,
            "message": "Usuario registrado exitosamente",
            "data": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "jdoe",
                "email": "jdoe@empresa.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+573001112233",
                "role": "b2c",
                "created_at": "2026-04-14T03:07:45Z"
            },
            "status": 201
        }
        """
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # req2: Retorna respuesta con estructura estándar
            return Response(
                format_response(
                    success=True,
                    message="Usuario registrado exitosamente",
                    data=serializer.data,
                    http_status=201,
                ),
                status=status.HTTP_201_CREATED,
            )
        # req2: Retorna respuesta de error con estructura estándar
        return Response(
            format_response(
                success=False,
                message="Error en la validación de datos",
                data=serializer.errors,
                http_status=400,
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserLoginView(APIView):
    """
    # (login) Endpoint para autenticación de usuarios con JWT
    # (login) Requisito 2: Usuario registrado obtiene tokens (access + refresh)
    # (login) POST /auth/login/ -> {"access": "token", "refresh": "token"}
    """

    permission_classes = [
        AllowAny
    ]  # (login) Público - no requiere autenticación previa

    @extend_schema(
        request=UserLoginSerializer,
        responses={
            200: OpenApiTypes.OBJECT,  # (login) Respuesta exitosa con tokens
            401: OpenApiTypes.OBJECT,  # (login) Credenciales inválidas
            400: OpenApiTypes.OBJECT,  # (login) Datos faltantes
        },
        parameters=[
            OpenApiParameter(
                name="x-api-key",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=False,
                description="API key requerida por el gateway.",
            ),
            OpenApiParameter(
                name="x-origin",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=False,
                description="Origen requerido por el gateway.",
            ),
        ],
    )
    def post(self, request):
        """
        # (login) POST /auth/login/ - Autentica usuario y retorna tokens JWT

        # (login) Request:
        {
            "username": "juan_perez",
            "password": "mi_password_seguro"
        }

        # (login) req2: Response 200 (exitoso con estructura estándar):
        {
            "success": true,
            "message": "Login exitoso",
            "data": {
                "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            },
            "status": 200
        }

        # (login) req2: Response 401 (credenciales inválidas con estructura estándar):
        {
            "success": false,
            "message": "Credenciales inválidas",
            "data": [],
            "status": 401
        }
        """
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            # (login) req2: Extrae tokens generados en la validación
            return Response(
                format_response(
                    success=True,
                    message="Login exitoso",
                    data={
                        "access": serializer.validated_data[
                            "access"
                        ],  # (login) Token JWT de acceso
                        "refresh": serializer.validated_data[
                            "refresh"
                        ],  # (login) Token JWT de refresh
                    },
                    http_status=200,
                ),
                status=status.HTTP_200_OK,  # (login) Retorna 200 OK
            )
        # (login) req2: Retorna errores con estructura estándar
        return Response(
            format_response(
                success=False,
                message="Credenciales inválidas",
                data=[],
                http_status=401,
            ),
            status=status.HTTP_401_UNAUTHORIZED,
        )


# (update) Vista para actualización parcial del perfil de usuario
class UserProfileUpdateView(APIView):  # (update)
    """
    # (update) Endpoint para actualizar perfil del usuario autenticado.
    # (update) Solo usuarios con JWT válido pueden acceder.
    # (update) PATCH /profile/update/ -> actualización parcial de campos.
    # (update) El campo email es de solo lectura (ignorado si se envía).
    """

    permission_classes = [IsAuthenticated]  # (update) Requiere JWT válido

    @extend_schema(  # (update)
        request=UserProfileUpdateSerializer,  # (update)
        responses={  # (update)
            200: OpenApiTypes.OBJECT,  # (update) Perfil actualizado
            400: OpenApiTypes.OBJECT,  # (update) Datos inválidos
            401: OpenApiTypes.OBJECT,  # (update) No autenticado
        },
        parameters=[  # (update)
            OpenApiParameter(  # (update)
                name="Authorization",  # (update)
                type=OpenApiTypes.STR,  # (update)
                location=OpenApiParameter.HEADER,  # (update)
                required=True,  # (update)
                description="Bearer <access_token> - Token JWT obtenido del login.",  # (update)
            ),
        ],
    )
    def patch(self, request):  # (update)
        """
        # (update) PATCH /profile/update/ - Actualiza perfil del usuario autenticado

        # (update) Request:
        {
            "first_name": "Juan",
            "last_name": "Pérez Actualizado"
        }

        # (update) Response 200:
        {
            "success": true,
            "message": "Perfil actualizado exitosamente",
            "data": {
                "id": "...",
                "username": "juan_perez",
                "email": "juan@example.com",
                "first_name": "Juan",
                "last_name": "Pérez Actualizado",
                ...
            },
            "status": 200
        }
        """
        user = request.user  # (update) Usuario autenticado desde el JWT
        serializer = UserProfileUpdateSerializer(  # (update)
            user, data=request.data, partial=True  # (update) partial=True para PATCH
        )
        if serializer.is_valid():  # (update)
            serializer.save()  # (update) Persiste cambios en BD
            return Response(  # (update)
                format_response(  # (update)
                    success=True,  # (update)
                    message="Perfil actualizado exitosamente",  # (update)
                    data=serializer.data,  # (update)
                    http_status=200,  # (update)
                ),
                status=status.HTTP_200_OK,  # (update)
            )
        return Response(  # (update)
            format_response(  # (update)
                success=False,  # (update)
                message="Error en la validación de datos",  # (update)
                data=serializer.errors,  # (update)
                http_status=400,  # (update)
            ),
            status=status.HTTP_400_BAD_REQUEST,  # (update)
        )


# (reset) Vista para solicitar restablecimiento de contraseña
class PasswordResetRequestView(APIView):  # (reset)
    """
    # (reset) Endpoint para solicitar reset de contraseña.
    # (reset) Genera un token único y envía un correo con el enlace.
    # (reset) POST /auth/password-reset/
    """

    permission_classes = [AllowAny]  # (reset) Público - no requiere autenticación

    @extend_schema(  # (reset)
        request=PasswordResetRequestSerializer,  # (reset)
        responses={200: OpenApiTypes.OBJECT},  # (reset)
    )
    def post(self, request):  # (reset)
        """
        # (reset) POST /auth/password-reset/ - Solicita reset de contraseña
        # (reset) Request: {"email": "juan@example.com"}
        # (reset) Response: {"success": true, "message": "Se ha enviado un correo..."}
        """
        serializer = PasswordResetRequestSerializer(data=request.data)  # (reset)
        if not serializer.is_valid():  # (reset)
            return Response(  # (reset)
                format_response(  # (reset)
                    success=False,  # (reset)
                    message="Email es requerido",  # (reset)
                    data=serializer.errors,  # (reset)
                    http_status=400,  # (reset)
                ),
                status=status.HTTP_400_BAD_REQUEST,  # (reset)
            )

        email = serializer.validated_data["email"]  # (reset)
        user = User.objects.filter(email=email).first()  # (reset)

        if user:  # (reset) Solo genera token si el usuario existe
            # (reset) Invalidar tokens anteriores no usados del mismo usuario
            PasswordResetToken.objects.filter(user=user, used=False).update(
                used=True
            )  # (reset)

            # (reset) Crear nuevo token
            reset_token = PasswordResetToken(user=user)  # (reset)
            reset_token.save()  # (reset)

            # (reset) Construir enlace de reset
            reset_link = (  # (reset)
                f"{request.scheme}://{request.get_host()}"  # (reset)
                f"/user/api/v1/auth/password-reset/confirm/?token={reset_token.token}"  # (reset)
            )

            # (reset) Enviar correo con el enlace
            send_mail(  # (reset)
                subject="Restablecimiento de contraseña",  # (reset)
                message=(  # (reset)
                    f"Hola {user.first_name},\n\n"  # (reset)
                    f"Recibimos una solicitud para restablecer tu contraseña.\n"  # (reset)
                    f"Usa el siguiente token para completar el proceso:\n\n"  # (reset)
                    f"Token: {reset_token.token}\n\n"  # (reset)
                    f"O usa este enlace:\n{reset_link}\n\n"  # (reset)
                    f"Este token expira en 1 hora.\n"  # (reset)
                    f"Si no solicitaste este cambio, ignora este correo."  # (reset)
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,  # (reset)
                recipient_list=[email],  # (reset)
                fail_silently=False,  # (reset)
            )

        # (reset) Siempre retorna éxito (no revela si el email existe o no)
        return Response(  # (reset)
            format_response(  # (reset)
                success=True,  # (reset)
                message="Se ha enviado un correo con las instrucciones.",  # (reset)
                http_status=200,  # (reset)
            ),
            status=status.HTTP_200_OK,  # (reset)
        )


# (reset) Vista para confirmar el cambio de contraseña con token
class PasswordResetConfirmView(APIView):  # (reset)
    """
    # (reset) Endpoint para confirmar reset de contraseña.
    # (reset) Valida el token y actualiza la contraseña.
    # (reset) POST /auth/password-reset/confirm/
    """

    permission_classes = [AllowAny]  # (reset) Público

    @extend_schema(  # (reset)
        request=PasswordResetConfirmSerializer,  # (reset)
        responses={  # (reset)
            200: OpenApiTypes.OBJECT,  # (reset)
            400: OpenApiTypes.OBJECT,  # (reset)
        },
    )
    def post(self, request):  # (reset)
        """
        # (reset) POST /auth/password-reset/confirm/ - Confirma cambio de contraseña
        # (reset) Request: {"token": "abc123...", "new_password": "NuevoPass123!"}
        # (reset) Response: {"success": true, "message": "Contraseña actualizada..."}
        """
        serializer = PasswordResetConfirmSerializer(data=request.data)  # (reset)
        if not serializer.is_valid():  # (reset)
            return Response(  # (reset)
                format_response(  # (reset)
                    success=False,  # (reset)
                    message="Error en la validación de datos",  # (reset)
                    data=serializer.errors,  # (reset)
                    http_status=400,  # (reset)
                ),
                status=status.HTTP_400_BAD_REQUEST,  # (reset)
            )

        token_value = serializer.validated_data["token"]  # (reset)
        new_password = serializer.validated_data["new_password"]  # (reset)

        # (reset) Buscar token en la base de datos
        reset_token = PasswordResetToken.objects.filter(  # (reset)
            token=token_value, used=False  # (reset)
        ).first()  # (reset)

        if not reset_token:  # (reset)
            return Response(  # (reset)
                format_response(  # (reset)
                    success=False,  # (reset)
                    message="Token inválido o ya utilizado",  # (reset)
                    http_status=400,  # (reset)
                ),
                status=status.HTTP_400_BAD_REQUEST,  # (reset)
            )

        # (reset) Verificar si el token ha expirado
        if not reset_token.is_valid():  # (reset)
            return Response(  # (reset)
                format_response(  # (reset)
                    success=False,  # (reset)
                    message="El token ha expirado. Solicita uno nuevo.",  # (reset)
                    http_status=400,  # (reset)
                ),
                status=status.HTTP_400_BAD_REQUEST,  # (reset)
            )

        # (reset) Actualizar contraseña del usuario
        user = reset_token.user  # (reset)
        user.set_password(new_password)  # (reset) Hashea la nueva contraseña
        user.save()  # (reset) Persiste en BD

        # (reset) Marcar token como usado
        reset_token.used = True  # (reset)
        reset_token.save()  # (reset)

        return Response(  # (reset)
            format_response(  # (reset)
                success=True,  # (reset)
                message="La contraseña ha sido actualizada exitosamente.",  # (reset)
                http_status=200,  # (reset)
            ),
            status=status.HTTP_200_OK,  # (reset)
        )
