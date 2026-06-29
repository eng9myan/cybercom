import logging

from django.core.cache import cache
from django.db import connection
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger("cybercom.health")


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "healthy"}, status=200)


class LivenessView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Quick ping to assert runtime process is alive
        return Response({"liveness": "alive"}, status=200)


class ReadinessView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        status = {}
        # 1. Test PostgreSQL Connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
            status["database"] = "up"
        except Exception as e:
            logger.error(f"Readiness check failed: Database offline. Details: {e}")
            status["database"] = "down"

        # 2. Test Cache / Redis Connection
        try:
            cache.set("health_check_key", "ok", timeout=5)
            if cache.get("health_check_key") == "ok":
                status["cache"] = "up"
            else:
                status["cache"] = "down"
        except Exception as e:
            logger.error(f"Readiness check failed: Cache offline. Details: {e}")
            status["cache"] = "down"

        overall_status = 200 if all(v == "up" for v in status.values()) else 503
        return Response(status, status=overall_status)
