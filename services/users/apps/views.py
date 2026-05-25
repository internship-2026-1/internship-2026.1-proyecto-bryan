from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserProfileUpdateSerializer,  # Importa serializer de perfil
    PasswordResetRequestSerializer,  # Importa serializer de solicitud de reset
    PasswordResetConfirmSerializer,  # Importa serializer de confirmación de reset
)  # Importa LoginSerializer
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)  # Importa IsAuthenticated
from .models import User, PasswordResetToken  # Importa modelos
from django.core.mail import send_mail  # Para enviar correos
from django.conf import settings  # Para acceder a configuración


# Helper function para estructurar respuestas API estándar
def format_response(success, message, data=None, http_status=200):
    """
    Formatea respuestas API con estructura estándar:
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
    """

    permission_classes = [AllowAny]  # Público - no requiere autenticación

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)

        # Si todo sale bien, retorna la respuesta con los datos del usuario
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                format_response(
                    success=True,
                    message="Usuario registrado exitosamente",
                    data=serializer.data,
                    http_status=201, # Para el usuario, 
                ),
                status=status.HTTP_201_CREATED, # Para el cliente, 
            )
        # Si hay errores de validación, retorna la respuesta con los errores
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
    # Endpoint para autenticación de usuarios con JWT
    # Requisito 2: Usuario registrado obtiene tokens (access + refresh)
    # POST /auth/login/ -> {"access": "token", "refresh": "token"}
    """

    permission_classes = [
        AllowAny
    ]  # Público - no requiere autenticación previa

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            # Extrae tokens generados en la validación
            return Response(
                format_response(
                    success=True,
                    message="Login exitoso",
                    data={
                        "access": serializer.validated_data["access"],
                        "refresh": serializer.validated_data["refresh"],
                        "role": serializer.validated_data["user"].role,
                    },
                    http_status=200,
                ),
                status=status.HTTP_200_OK,  # Retorna 200 OK
            )
        # Retorna errores con estructura estándar
        return Response(
            format_response(
                success=False,
                message="Credenciales inválidas",
                data=[],
                http_status=401,
            ),
            status=status.HTTP_401_UNAUTHORIZED,
        )


# Vista para actualización parcial del perfil de usuario
class UserProfileUpdateView(APIView):  
    """
    # Endpoint para actualizar perfil del usuario autenticado.
    # Solo usuarios con JWT válido pueden acceder.
    # PATCH /profile/update/ -> actualización parcial de campos.
    # El campo email es de solo lectura (ignorado si se envía).
    """

    permission_classes = [IsAuthenticated]  # Requiere JWT válido

    def patch(self, request):
        user = request.user  
        serializer = UserProfileUpdateSerializer(  
            user, data=request.data, partial=True  
        )
        if serializer.is_valid():  
            serializer.save()  
            return Response(  
                format_response(  
                    success=True,  
                    message="Perfil actualizado exitosamente",  
                    data=serializer.data,  
                    http_status=200,  
                ),
                status=status.HTTP_200_OK,  
            )
        return Response(  
            format_response(  
                success=False,  
                message="Error en la validación de datos",  
                data=serializer.errors,  
                http_status=400,  
            ),
            status=status.HTTP_400_BAD_REQUEST,  
        )


# Vista para solicitar restablecimiento de contraseña
class PasswordResetRequestView(APIView):  
    """
    # Endpoint para solicitar reset de contraseña.
    # Genera un token único y envía un correo con el enlace.
    # POST /auth/password-reset/
    """

    permission_classes = [AllowAny]  

    def post(self, request):
        """
        POST /auth/password-reset/ - Solicita reset de contraseña
        """
        serializer = PasswordResetRequestSerializer(data=request.data)  
        if not serializer.is_valid():  
            return Response(  
                format_response(  
                    success=False,  
                    message="Email es requerido",  
                    data=serializer.errors,  
                    http_status=400,  
                ),
                status=status.HTTP_400_BAD_REQUEST,  
            )

        email = serializer.validated_data["email"]  
        user = User.objects.filter(email=email).first()  

        if user:  
            # Invalidar tokens anteriores no usados del mismo usuario
            PasswordResetToken.objects.filter(user=user, used=False).update(
                used=True
            )  

            # Crear nuevo token
            reset_token = PasswordResetToken(user=user)  
            reset_token.save()  

            # Construir enlace de reset
            frontend_url = settings.FRONTEND_URL.rstrip("/")
            reset_link = f"{frontend_url}/reset-password?token={reset_token.token}"

            # Enviar correo con el enlace
            send_mail(  
                subject="Restablecimiento de contraseña",  
                message=(  
                    f"Hola {user.first_name},\n\n"  
                    f"Recibimos una solicitud para restablecer tu contraseña.\n"  
                    f"Usa el siguiente token para completar el proceso:\n\n"  
                    f"Token: {reset_token.token}\n\n"  
                    f"O usa este enlace:\n{reset_link}\n\n"  
                    f"Este token expira en 1 hora.\n"  
                    f"Si no solicitaste este cambio, ignora este correo."  
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,  
                recipient_list=[email],  
                fail_silently=False,  
            )

        # Siempre retorna éxito (no revela si el email existe o no)
        return Response(  
            format_response(  
                success=True,  
                message="Se ha enviado un correo con las instrucciones.",  
                http_status=200,  
            ),
            status=status.HTTP_200_OK,  
        )


# Vista para confirmar el cambio de contraseña con token
class PasswordResetConfirmView(APIView):  
    """
    # Endpoint para confirmar reset de contraseña.
    # Valida el token y actualiza la contraseña.
    # POST /auth/password-reset/confirm/
    """

    permission_classes = [AllowAny]  

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)  
        if not serializer.is_valid():  
            return Response(  
                format_response(  
                    success=False,  
                    message="Error en la validación de datos",  
                    data=serializer.errors,  
                    http_status=400,  
                ),
                status=status.HTTP_400_BAD_REQUEST,  
            )

        token_value = serializer.validated_data["token"]  
        new_password = serializer.validated_data["new_password"]  

        # Buscar token en la base de datos
        reset_token = PasswordResetToken.objects.filter(  
            token=token_value, used=False  
        ).first()  

        if not reset_token:  
            return Response(  
                format_response(  
                    success=False,  
                    message="Token inválido o ya utilizado",  
                    http_status=400,  
                ),
                status=status.HTTP_400_BAD_REQUEST,  
            )

        # Verificar si el token ha expirado
        if not reset_token.is_valid():  
            return Response(  
                format_response(  
                    success=False,  
                    message="El token ha expirado. Solicita uno nuevo.",  
                    http_status=400,  
                ),
                status=status.HTTP_400_BAD_REQUEST,  
            )

        # Actualizar contraseña del usuario
        user = reset_token.user  
        user.set_password(new_password)  
        user.save()  

        # Marcar token como usado
        reset_token.used = True  
        reset_token.save()  

        return Response(  
            format_response(  
                success=True,  
                message="La contraseña ha sido actualizada exitosamente.",  
                http_status=200,  
            ),
            status=status.HTTP_200_OK,  
        )


class UserListView(APIView):
    """GET /users/ - Lista todos los usuarios (requiere autenticación)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.all().order_by("-date_joined")
        data = [
            {
                "id": str(u.id),
                "name": f"{u.first_name} {u.last_name}".strip() or u.username,
                "email": u.email,
                "role": u.role,
                "status": "Activo" if u.is_active else "Inactivo",
                "createdAt": u.date_joined.strftime("%Y-%m-%d"),
            }
            for u in users
        ]
        return Response(
            format_response(success=True, message="Usuarios obtenidos", data=data, http_status=200),
            status=status.HTTP_200_OK,
        )
