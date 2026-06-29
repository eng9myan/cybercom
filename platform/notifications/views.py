from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, NotificationTemplate
from .serializers import (
    NotificationSerializer,
    NotificationTemplateSerializer,
    SendFromTemplateSerializer,
    SendNotificationSerializer,
)
from .services import NotificationService


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        if not tenant_id:
            return Response({"detail": "Tenant context required"}, status=400)
        qs = Notification.objects.filter(tenant_id=tenant_id).order_by("-created_at")[:100]
        return Response(NotificationSerializer(qs, many=True).data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        if not tenant_id:
            return Response({"detail": "Tenant context required"}, status=400)
        ser = SendNotificationSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        notification = NotificationService.send(
            tenant_id=str(tenant_id),
            recipient_id=d["recipient_id"],
            recipient_address=d["recipient_address"],
            channel=d["channel"],
            subject=d.get("subject", ""),
            body=d["body"],
            scheduled_at=d.get("scheduled_at"),
            metadata=d.get("metadata", {}),
        )
        return Response(NotificationSerializer(notification).data, status=201)


class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        try:
            notification = Notification.objects.get(id=pk, tenant_id=tenant_id)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        return Response(NotificationSerializer(notification).data)


class NotificationSendFromTemplateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        if not tenant_id:
            return Response({"detail": "Tenant context required"}, status=400)
        ser = SendFromTemplateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        notification = NotificationService.send_from_template(
            tenant_id=str(tenant_id),
            template_name=d["template_name"],
            channel=d["channel"],
            recipient_id=d["recipient_id"],
            recipient_address=d["recipient_address"],
            context=d["context"],
            lang=d.get("lang", "en"),
        )
        if not notification:
            return Response({"detail": "Template not found or inactive"}, status=404)
        return Response(NotificationSerializer(notification).data, status=201)


class TemplateListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        qs = NotificationTemplate.objects.filter(tenant_id=tenant_id, is_active=True)
        return Response(NotificationTemplateSerializer(qs, many=True).data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        if not tenant_id:
            return Response({"detail": "Tenant context required"}, status=400)
        ser = NotificationTemplateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        template = ser.save(tenant_id=tenant_id)
        return Response(NotificationTemplateSerializer(template).data, status=201)


class TemplateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        try:
            template = NotificationTemplate.objects.get(id=pk, tenant_id=tenant_id)
        except NotificationTemplate.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        return Response(NotificationTemplateSerializer(template).data)

    def put(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        try:
            template = NotificationTemplate.objects.get(id=pk, tenant_id=tenant_id)
        except NotificationTemplate.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        ser = NotificationTemplateSerializer(template, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)
