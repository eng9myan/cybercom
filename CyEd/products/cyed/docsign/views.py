from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.docsign.models import (
    SignableDocument, Signatory, SignatureAuditEvent, content_hash_of, write_signature_audit,
)
from products.cyed.docsign.serializers import (
    SignableDocumentSerializer, SignatorySerializer, SignatureAuditEventSerializer,
)
from products.cyed.governance.access import ADMIN, LEADERSHIP, IsStaff, _email, has_any, is_staff


def _client_ip(request) -> str:
    fwd = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if fwd:
        return fwd.split(",")[0].strip()[:64]
    return (request.META.get("REMOTE_ADDR") or "")[:64]


class SignableDocumentViewSet(TenantScopedModelViewSet):
    """
    Documents requiring signature. Staff author and send them; any authenticated
    party listed as a signatory may view and sign their own document.
    """

    queryset = SignableDocument.objects.prefetch_related("signatories").all()
    serializer_class = SignableDocumentSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve", "sign", "decline", "audit"):
            return [IsAuthenticatedViaClaims()]
        return [IsStaff()]

    def get_queryset(self):
        qs = super().get_queryset()
        # Non-staff only ever see documents they are a signatory on.
        if not is_staff(self.request):
            email = _email(self.request)
            qs = qs.filter(signatories__email__iexact=email).distinct() if email else qs.none()
        params = self.request.query_params
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("doc_type"):
            qs = qs.filter(doc_type=params["doc_type"])
        return qs

    def perform_create(self, serializer):
        doc = serializer.save(tenant_id=self.request.tenant_id, created_by=_email(self.request))
        write_signature_audit(doc, "created", actor=_email(self.request), ip=_client_ip(self.request))

    @action(detail=True, methods=["post"], url_path="signatories")
    def add_signatory(self, request, pk=None):
        doc = self.get_object()
        if doc.status not in ("draft",):
            return Response({"detail": "Signatories can only be added while the document is a draft."},
                            status=status.HTTP_400_BAD_REQUEST)
        ser = SignatorySerializer(data={**request.data, "document": str(doc.id)})
        ser.is_valid(raise_exception=True)
        ser.save(tenant_id=request.tenant_id)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        doc = self.get_object()
        if doc.status != "draft":
            return Response({"detail": "Only a draft document can be sent."}, status=400)
        if not doc.signatories.exists():
            return Response({"detail": "Add at least one signatory before sending."}, status=400)
        doc.content_hash = content_hash_of(doc.title, doc.body)  # seal
        doc.status = "sent"
        doc.sent_at = timezone.now()
        doc.save()
        write_signature_audit(doc, "sent", actor=_email(request),
                              detail=f"Sent to {doc.signatories.count()} signatory(ies)", ip=_client_ip(request))
        # Notify each signatory through the existing notifications seam.
        # Best-effort: a delivery failure must never block the signing workflow.
        try:
            from products.cyed.notifications.delivery import deliver
            from products.cyed.notifications.models import Notification

            for s in doc.signatories.all():
                n = Notification.objects.create(
                    tenant_id=doc.tenant_id,
                    student=doc.student,
                    recipient_kind="guardian" if s.role == "parent" else "staff",
                    recipient_name=s.name,
                    recipient_email=s.email,
                    channel="in_app",
                    category="general",
                    subject=f"Signature requested: {doc.title}",
                    body=f"You have been asked to sign '{doc.title}'."
                         + (f" Due {doc.due_date}." if doc.due_date else ""),
                    related_model="cyed_docsign.SignableDocument",
                    related_id=str(doc.id),
                    status="queued",
                )
                deliver(n)
        except Exception:
            pass
        return Response(SignableDocumentSerializer(doc).data)

    def _my_signatory(self, doc, request):
        email = _email(request)
        if not email:
            return None
        return doc.signatories.filter(email__iexact=email).first()

    @action(detail=True, methods=["post"])
    def sign(self, request, pk=None):
        doc = self.get_object()
        if doc.status not in ("sent", "partially_signed"):
            return Response({"detail": f"Document is '{doc.status}' and cannot be signed."}, status=400)
        if not doc.verify():
            return Response({"detail": "Document body was altered after sending; signing is blocked."}, status=409)
        sig = self._my_signatory(doc, request)
        if sig is None:
            return Response({"detail": "You are not a signatory on this document."},
                            status=status.HTTP_403_FORBIDDEN)
        if sig.status != "pending":
            return Response({"detail": f"You have already {sig.status} this document."}, status=400)

        # Sequential signing: everyone with a lower order must have signed first.
        earlier = doc.signatories.filter(order__lt=sig.order).exclude(status="signed")
        if earlier.exists():
            return Response({"detail": "An earlier signatory has not signed yet."}, status=400)

        typed = (request.data.get("typed_signature") or "").strip()
        if not typed:
            return Response({"typed_signature": "Type your full name to sign."}, status=400)

        sig.status = "signed"
        sig.signed_at = timezone.now()
        sig.typed_signature = typed[:255]
        sig.signed_hash = doc.content_hash
        sig.ip_address = _client_ip(request)
        sig.save()
        write_signature_audit(doc, "signed", actor=sig.email, signatory=sig,
                              detail=f"Signed as '{typed}'", ip=sig.ip_address)
        doc.refresh_status()
        return Response(SignableDocumentSerializer(doc).data)

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        doc = self.get_object()
        sig = self._my_signatory(doc, request)
        if sig is None:
            return Response({"detail": "You are not a signatory on this document."}, status=403)
        if sig.status != "pending":
            return Response({"detail": f"You have already {sig.status} this document."}, status=400)
        sig.status = "declined"
        sig.decline_reason = (request.data.get("reason") or "")[:255]
        sig.save()
        write_signature_audit(doc, "declined", actor=sig.email, signatory=sig,
                              detail=sig.decline_reason, ip=_client_ip(request))
        doc.refresh_status()
        return Response(SignableDocumentSerializer(doc).data)

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        if not has_any(request, ADMIN | LEADERSHIP):
            return Response({"detail": "Only leadership may void a document."}, status=403)
        doc = self.get_object()
        doc.status = "voided"
        doc.save()
        write_signature_audit(doc, "voided", actor=_email(request),
                              detail=(request.data.get("reason") or "")[:500], ip=_client_ip(request))
        return Response(SignableDocumentSerializer(doc).data)

    @action(detail=True, methods=["get"])
    def audit(self, request, pk=None):
        doc = self.get_object()
        events = doc.audit_events.all()
        return Response({
            "document": str(doc.id),
            "title": doc.title,
            "status": doc.status,
            "verified": doc.verify(),
            "content_hash": doc.content_hash,
            "events": SignatureAuditEventSerializer(events, many=True).data,
        })


class SignatoryViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    serializer_class = SignatorySerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = Signatory.objects.filter(tenant_id=self.request.tenant_id).select_related("document")
        if self.request.query_params.get("status"):
            qs = qs.filter(status=self.request.query_params["status"])
        return qs


class SignatureAuditEventViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """Read-only: the trail is append-only by design."""

    serializer_class = SignatureAuditEventSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        return SignatureAuditEvent.objects.filter(tenant_id=self.request.tenant_id)
