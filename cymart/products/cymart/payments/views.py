from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Dispute, PaymentIntent
from .serializers import DisputeSerializer, PaymentIntentSerializer
from .services import DisputeService, PaymentError, PaymentService


class PaymentIntentViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only — intents are created via checkout, not raw POST here."""

    queryset = PaymentIntent.objects.all().order_by("-created_at")
    serializer_class = PaymentIntentSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"])
    def capture(self, request, pk=None):
        intent = self.get_object()
        try:
            intent = PaymentService().capture(intent, amount=request.data.get("amount"))
        except PaymentError as exc:
            return Response({"detail": str(exc)}, status=409)
        return Response(self.get_serializer(intent).data)

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        intent = self.get_object()
        try:
            intent = PaymentService().refund(intent, amount=request.data.get("amount"))
        except PaymentError as exc:
            return Response({"detail": str(exc)}, status=409)
        return Response(self.get_serializer(intent).data)


class DisputeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Dispute.objects.all().order_by("-created_at")
    serializer_class = DisputeSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        dispute = self.get_object()
        try:
            dispute = DisputeService().resolve(
                dispute, in_favor_of=request.data["in_favor_of"], notes=request.data.get("notes", "")
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(self.get_serializer(dispute).data)
