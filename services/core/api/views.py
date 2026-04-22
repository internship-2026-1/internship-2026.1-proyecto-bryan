from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


# (c) Endpoint de health check para verificar disponibilidad del servicio
class HealthCheckView(APIView):
    """
    Health check endpoint que verifica la disponibilidad del servicio Core.
    """

    def get(self, request):
        """GET /api/v1/health/ - Retorna el estado del servicio"""
        return Response(
            {
                "success": True,
                "message": "Core service healthy.",
                "data": {"service": "core", "health": "ok"},
                "status": 200,
            },
            status=status.HTTP_200_OK,
        )
