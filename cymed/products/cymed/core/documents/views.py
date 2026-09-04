from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from products.cymed.core.documents.models import ClinicalDocument
from products.cymed.core.documents.serializers import ClinicalDocumentSerializer


class ClinicalDocumentViewSet(viewsets.ModelViewSet):
    queryset = ClinicalDocument.objects.all()
    serializer_class = ClinicalDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    @action(detail=True, methods=["post"])
    def sign(self, request, pk=None):
        """Digitally signs and finalizes a clinical document."""
        doc = self.get_object()
        if doc.status == "final":
            return Response(
                {"detail": "Document is already signed and finalized."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        doc.status = "final"
        doc.digitally_signed_by = str(request.user)
        doc.signed_at = timezone.now()
        doc.save()

        # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
        from platform.canonical import events as canonical_events

        canonical_events.emit(
            event_type="cymed.document.signed",
            aggregate_type="ClinicalDocument",
            aggregate_id=doc.id,
            tenant_id=doc.tenant_id,
            payload={
                "document_id": str(doc.id),
                "patient_id": str(doc.patient.id),
                "signed_by": doc.digitally_signed_by,
                "signed_at": doc.signed_at.isoformat(),
            },
        )

        return Response(
            {
                "status": doc.status,
                "signed_by": doc.digitally_signed_by,
                "signed_at": doc.signed_at,
            },
            status=status.HTTP_200_OK,
        )
