"""
Push device registration and newsletters.

Kept apart from `views.py`, which serves a person's own notification inbox.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import IsStaff, _email
from products.cyed.notifications import newsletters
from products.cyed.notifications.models import Newsletter, PushDevice
from products.cyed.notifications.serializers import (
    NewsletterSerializer,
    PushDeviceSerializer,
)


class PushDeviceViewSet(TenantScopedModelViewSet):
    """
    Devices that have agreed to receive push notifications.

    Anyone signed in may register their own device and see only their own —
    a list of everybody's subscriptions would be a map of who uses what.
    """

    queryset = PushDevice.objects.all()
    serializer_class = PushDeviceSerializer
    permission_classes = [IsAuthenticatedViaClaims]

    def get_queryset(self):
        # Scoped to the caller regardless of role: staff have no reason to read
        # another person's device tokens, and a token is a credential.
        return super().get_queryset().filter(owner_email__iexact=_email(self.request))

    def perform_create(self, serializer):
        """
        Register against the authenticated email, never one from the body.

        Re-registering the same token reactivates the row rather than failing:
        a browser that was revoked and re-granted sends the same subscription
        back, and a school should not need support to fix that.
        """
        token = serializer.validated_data.get("token", "")
        existing = PushDevice.objects.filter(
            tenant_id=self.request.tenant_id, token=token
        ).first()
        if existing is not None:
            existing.is_active = True
            existing.failed_at = None
            existing.failure_reason = ""
            existing.owner_email = _email(self.request)
            existing.save(update_fields=[
                "is_active", "failed_at", "failure_reason", "owner_email", "updated_at",
            ])
            serializer.instance = existing
            return
        serializer.save(
            tenant_id=self.request.tenant_id, owner_email=_email(self.request)
        )

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """Turn notifications off for one device without forgetting it."""
        device = self.get_object()
        device.is_active = False
        device.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(device).data)


class NewsletterViewSet(TenantScopedModelViewSet):
    """
    Bulk messages to an audience. Staff compose and send; families read theirs
    in their ordinary notification inbox.
    """

    queryset = Newsletter.objects.select_related("campus").all()
    serializer_class = NewsletterSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("status"):
            qs = qs.filter(status=self.request.query_params["status"])
        return qs

    @action(detail=True, methods=["get"])
    def preview(self, request, pk=None):
        """
        How many people this would reach, before anybody presses send.

        "All parents" and "Year 9 parents" look identical on a form and differ
        by nine hundred recipients.
        """
        return Response(newsletters.preview(self.get_object()))

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        """Fan out and deliver. Refuses a second send."""
        try:
            newsletter = newsletters.send(self.get_object(), sent_by=_email(request))
        except newsletters.NewsletterError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(newsletter).data)

    @action(detail=True, methods=["get"], url_path="delivery-report")
    def delivery_report(self, request, pk=None):
        """
        What actually happened — counted from the notification rows, so a
        message that failed at the provider is reported as failed here.
        """
        return Response(newsletters.delivery_report(self.get_object()))
