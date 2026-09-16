"""
Payments API surface.

Two distinct audiences, deliberately split:

  * Staff/parents call the authenticated `/api/v1/payments/...` routes with a
    bearer token and a tenant header, like every other CyEd endpoint.
  * The gateway calls `/api/v1/public/payments/webhook/<provider>/` with neither
    — it has no CyEd account and no idea what a tenant is. That route is
    authenticated by HMAC over the raw body instead, and resolves the tenant
    from the intent the event refers to.

Who may do what:
  create   — a parent may open an intent, but only against an invoice or
             installment belonging to a child they can already see.
  capture  — finance/leadership only. This is the "the money arrived" assertion
             and a parent must never be able to make it about themselves.
  refund   — finance/leadership only.
  reconcile/report/webhook log — finance/leadership only.
"""

from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import (
    IsFinanceOrLeadership,
    is_staff,
    visible_student_ids,
)
from products.cyed.payments import services
from products.cyed.payments.models import PaymentIntent, WebhookEvent
from products.cyed.payments.providers import (
    PaymentProviderError,
    ProviderNotConfigured,
    available_providers,
    configured_provider_name,
)
from products.cyed.payments.serializers import (
    PaymentIntentCreateSerializer,
    PaymentIntentSerializer,
    RefundSerializer,
    WebhookEventSerializer,
)


def _bad(exc, code=status.HTTP_400_BAD_REQUEST):
    return Response({"detail": str(exc)}, status=code)


class PaymentIntentViewSet(TenantScopedModelViewSet):
    queryset = PaymentIntent.objects.select_related(
        "invoice", "invoice__student", "installment", "installment__bill", "installment__bill__student"
    ).prefetch_related("refunds").all()
    serializer_class = PaymentIntentSerializer
    # No PUT/PATCH: an intent's state belongs to the gateway and the service
    # layer. Everything a client may legitimately change happens through an
    # action below, where the business rules live.
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve", "create", "providers"):
            return [IsAuthenticatedViaClaims()]
        return [IsFinanceOrLeadership()]

    def get_queryset(self):
        """
        Scope non-staff callers to intents for their own children.

        An intent can hang off an invoice OR an installment, so the student
        reachable from it lives at one of two paths — hence the Q. Unlinked
        intents (donations, uniform sales) have no student and are staff-only.
        """
        qs = super().get_queryset()
        visible = visible_student_ids(self.request, self.request.tenant_id)
        if visible is not None:
            qs = qs.filter(
                Q(invoice__student_id__in=visible)
                | Q(installment__bill__student_id__in=visible)
            )
        params = self.request.query_params
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("invoice"):
            qs = qs.filter(invoice_id=params["invoice"])
        if params.get("installment"):
            qs = qs.filter(installment_id=params["installment"])
        if params.get("unreconciled") == "1":
            qs = qs.filter(status="succeeded", reconciled_at__isnull=True)
        return qs

    # ── creation ─────────────────────────────────────────────────────────────
    def create(self, request, *args, **kwargs):
        payload = PaymentIntentCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        invoice = installment = None
        if data.get("invoice"):
            invoice = self._resolve_target("invoice", data["invoice"])
            if invoice is None:
                return _bad("No such invoice, or you may not pay it.", status.HTTP_404_NOT_FOUND)
        if data.get("installment"):
            installment = self._resolve_target("installment", data["installment"])
            if installment is None:
                return _bad("No such installment, or you may not pay it.", status.HTTP_404_NOT_FOUND)

        session = getattr(request, "user_session", None) or {}
        try:
            intent, created = services.create_intent(
                tenant_id=request.tenant_id,
                amount=data["amount"],
                idempotency_key=data["idempotency_key"],
                currency=data.get("currency") or "AUD",
                method=data.get("method") or "card",
                provider=data.get("provider") or None,
                invoice=invoice,
                installment=installment,
                payer_email=data.get("payer_email") or session.get("email", "") or "",
                description=data.get("description", ""),
                created_by=session.get("email", "") or "",
                metadata=data.get("metadata") or {},
            )
        except services.PaymentError as exc:
            return _bad(exc)
        except ProviderNotConfigured as exc:
            # The deployment is misconfigured, not the request. 503 so a client
            # retries rather than treating this as its own fault.
            return _bad(exc, status.HTTP_503_SERVICE_UNAVAILABLE)
        except PaymentProviderError as exc:
            return _bad(exc, status.HTTP_502_BAD_GATEWAY)

        # 200 (not 201) on an idempotent replay: nothing new was created, and
        # the client must be able to tell the difference.
        return Response(
            self.get_serializer(intent).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def _resolve_target(self, kind: str, target_id):
        """
        Fetch the invoice/installment being paid, honouring the caller's own
        visibility. Returns None if it does not exist *or* is not theirs — the
        two are deliberately indistinguishable to the caller, so this endpoint
        cannot be used to enumerate other families' invoices.
        """
        tenant_id = self.request.tenant_id
        visible = visible_student_ids(self.request, tenant_id)
        if kind == "invoice":
            from products.cyed.fees.models import Invoice

            qs = Invoice.objects.filter(id=target_id)
            if tenant_id is not None:
                qs = qs.filter(tenant_id=tenant_id)
            if visible is not None:
                qs = qs.filter(student_id__in=visible)
            return qs.first()

        from products.cyed.billing.models import Installment

        qs = Installment.objects.filter(id=target_id)
        if tenant_id is not None:
            qs = qs.filter(tenant_id=tenant_id)
        if visible is not None:
            qs = qs.filter(bill__student_id__in=visible)
        return qs.first()

    # ── money movement ───────────────────────────────────────────────────────
    @action(detail=True, methods=["post"])
    def capture(self, request, pk=None):
        """Finance confirms the money landed (BPAY/transfer) or captures an auth."""
        intent = self.get_object()
        try:
            intent = services.capture_intent(
                intent,
                amount=request.data.get("amount"),
                actor=(getattr(request, "user_session", None) or {}).get("email", ""),
            )
        except services.PaymentError as exc:
            return _bad(exc)
        except ProviderNotConfigured as exc:
            return _bad(exc, status.HTTP_503_SERVICE_UNAVAILABLE)
        except PaymentProviderError as exc:
            return _bad(exc, status.HTTP_502_BAD_GATEWAY)
        return Response(self.get_serializer(intent).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        intent = self.get_object()
        try:
            intent = services.cancel_intent(intent, reason=request.data.get("reason", ""))
        except services.PaymentError as exc:
            return _bad(exc)
        return Response(self.get_serializer(intent).data)

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        intent = self.get_object()
        try:
            refund = services.refund_intent(
                intent,
                amount=request.data.get("amount"),
                reason=request.data.get("reason", ""),
                actor=(getattr(request, "user_session", None) or {}).get("email", ""),
            )
        except services.PaymentError as exc:
            return _bad(exc)
        except ProviderNotConfigured as exc:
            return _bad(exc, status.HTTP_503_SERVICE_UNAVAILABLE)
        except PaymentProviderError as exc:
            return _bad(exc, status.HTTP_502_BAD_GATEWAY)
        # A failed refund is a real, recorded outcome — 200 with the row, so the
        # finance officer can see why, rather than an opaque error.
        body = RefundSerializer(refund).data
        body["intent"] = self.get_serializer(intent).data
        return Response(body, status=status.HTTP_201_CREATED if refund.status == "succeeded" else status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def reconcile(self, request, pk=None):
        """Re-run ledger posting for one intent. Safe to call repeatedly."""
        intent = self.get_object()
        result = services.reconcile_intent(intent)
        intent.refresh_from_db()
        return Response({"applied": result, "intent": self.get_serializer(intent).data})

    # ── operational reporting ────────────────────────────────────────────────
    @action(detail=False, methods=["get"], url_path="reconciliation-report")
    def reconciliation_report(self, request):
        """
        Every intent whose state disagrees with the ledger it points at.
        An empty `rows` is the finance office's daily green light.
        """
        rows = services.reconciliation_report(request.tenant_id, queryset=self.get_queryset())
        return Response({"count": len(rows), "rows": rows})

    @action(detail=False, methods=["get"])
    def providers(self, request):
        return Response({
            "configured": configured_provider_name(),
            "available": available_providers(),
        })


class WebhookEventViewSet(TenantScopedModelViewSet):
    """
    Read-only audit of every provider callback, including rejected ones.

    Forged and malformed events are recorded against a sentinel tenant, so a
    tenant-scoped list would hide exactly the rows a security review needs.
    `?all=1` lifts the scope for admin/leadership.
    """

    queryset = WebhookEvent.objects.select_related("intent").all()
    serializer_class = WebhookEventSerializer
    permission_classes = [IsFinanceOrLeadership]
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        if self.request.query_params.get("all") == "1" and is_staff(self.request):
            qs = WebhookEvent.objects.select_related("intent").all()
        else:
            qs = super().get_queryset()
        params = self.request.query_params
        if params.get("result"):
            qs = qs.filter(result=params["result"])
        if params.get("provider"):
            qs = qs.filter(provider=params["provider"])
        if params.get("rejected") == "1":
            qs = qs.filter(verified=False)
        return qs


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def payment_webhook(request, provider: str):
    """
    Inbound gateway callback. Public by necessity, authenticated by HMAC.

    `request.body` — the untouched bytes — is what the signature covers; using
    the parsed-and-reserialised body would change key order and whitespace and
    break every legitimate signature. The status code comes from the service
    layer, which distinguishes "we rejected you" (4xx) from "we are not
    configured to accept you" (503) from "understood, nothing to do" (200).
    """
    adapter_header = None
    try:
        from products.cyed.payments.providers import get_provider

        adapter_header = get_provider(provider).signature_header
    except ProviderNotConfigured:
        adapter_header = "HTTP_X_CYED_SIGNATURE"

    signature = request.META.get(adapter_header, "") or request.META.get("HTTP_X_CYED_SIGNATURE", "")
    event, http_status = services.apply_webhook(request.body, signature, provider_name=provider)
    return Response(
        {"result": event.result, "detail": event.detail, "event": str(event.id)},
        status=http_status,
    )
