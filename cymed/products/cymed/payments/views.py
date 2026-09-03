"""REST endpoints for payments/insurance/delegated-pay per P0-2 §6."""
import secrets
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from products.cymed.patient_portal.models import PatientPortalProfile

from .models import (
    EligibilityCheck,
    InsurancePolicy,
    PatientWallet,
    PaymentMethod,
    PaymentRequest,
    PaymentTransaction,
    PreAuthorization,
    UnifiedBill,
)
from .serializers import (
    EligibilityCheckSerializer,
    InsurancePolicySerializer,
    PatientWalletSerializer,
    PaymentMethodSerializer,
    PaymentRequestSerializer,
    PaymentTransactionSerializer,
    PreAuthorizationSerializer,
    UnifiedBillSerializer,
)
from .services import check_eligibility, pay_bill, submit_preauth


# ── Bills ───────────────────────────────────────────────────────────────
class UnifiedBillViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UnifiedBill.objects.all().prefetch_related("line_items")
    serializer_class = UnifiedBillSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        scope = self.request.query_params.get("scope", "own")
        # TODO: filter by authenticated user's profile / delegations
        return qs

    @action(detail=True, methods=["post"], url_path="pay")
    def pay(self, request, pk=None):
        method_id = request.data.get("method_id")
        amount = request.data.get("amount")
        on_behalf_of = request.data.get("on_behalf_of", "")
        if not method_id:
            return Response({"detail": "method_id required"}, status=400)
        payer = self._get_current_profile(request)
        if not payer:
            return Response({"detail": "No patient profile for user"}, status=403)
        txn = pay_bill(
            bill_id=pk,
            method_id=method_id,
            payer_profile_id=payer.id,
            amount=Decimal(str(amount)) if amount is not None else None,
            on_behalf_note=on_behalf_of,
        )
        return Response(PaymentTransactionSerializer(txn).data, status=202)

    @action(detail=True, methods=["post"], url_path="payment-request")
    def request_payment(self, request, pk=None):
        bill = self.get_object()
        requester = self._get_current_profile(request)
        if not requester:
            return Response({"detail": "No profile"}, status=403)
        payer_phone = request.data.get("payer_phone", "")
        payer_email = request.data.get("payer_email", "")
        amount = Decimal(str(request.data.get("amount", bill.patient_due)))
        pr = PaymentRequest.objects.create(
            bill=bill,
            requester_profile=requester,
            payer_phone=payer_phone,
            payer_email=payer_email,
            amount=amount,
            token=secrets.token_urlsafe(48),
            expires_at=timezone.now() + timedelta(hours=48),
        )
        # TODO: cyintegrationhub sends SMS/WhatsApp with the link
        return Response(PaymentRequestSerializer(pr).data, status=201)

    @staticmethod
    def _get_current_profile(request):
        if not request.user.is_authenticated:
            return None
        return PatientPortalProfile.objects.filter(user_id=request.user.id).first()


# ── Payment Request public endpoints ────────────────────────────────────
class PaymentRequestPublicView(APIView):
    """Non-authenticated payer views + pays a delegated request."""
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            pr = PaymentRequest.objects.select_related("bill", "requester_profile").get(token=token)
        except PaymentRequest.DoesNotExist:
            return Response({"detail": "Invalid link"}, status=404)
        if pr.used_at:
            return Response({"detail": "Link already used"}, status=410)
        if pr.expires_at < timezone.now():
            return Response({"detail": "Link expired"}, status=410)
        return Response({
            "amount": str(pr.amount),
            "requester_name": str(pr.requester_profile.patient),
            "bill_number": pr.bill.bill_number,
            "expires_at": pr.expires_at,
        })

    def post(self, request, token):
        try:
            pr = PaymentRequest.objects.select_related("bill").get(token=token)
        except PaymentRequest.DoesNotExist:
            return Response({"detail": "Invalid link"}, status=404)
        if pr.used_at:
            return Response({"detail": "Already used"}, status=410)
        if pr.expires_at < timezone.now():
            return Response({"detail": "Expired"}, status=410)

        method_id = request.data.get("method_id")
        payer_profile_id = request.data.get("payer_profile_id")
        if not (method_id and payer_profile_id):
            return Response({"detail": "method_id + payer_profile_id required"}, status=400)

        txn = pay_bill(
            bill_id=pr.bill.id,
            method_id=method_id,
            payer_profile_id=payer_profile_id,
            amount=pr.amount,
            on_behalf_note=f"PaymentRequest {pr.token[:8]}",
        )
        pr.used_at = timezone.now()
        pr.transaction = txn
        pr.save(update_fields=["used_at", "transaction"])
        return Response(PaymentTransactionSerializer(txn).data, status=201)


# ── Payment methods ─────────────────────────────────────────────────────
class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.filter(is_deleted=False)
    serializer_class = PaymentMethodSerializer

    @action(detail=True, methods=["post"], url_path="default")
    def set_default(self, request, pk=None):
        m = self.get_object()
        PaymentMethod.objects.filter(profile=m.profile).update(is_default=False)
        m.is_default = True
        m.save(update_fields=["is_default", "updated_at"])
        return Response({"status": "default"})


# ── Wallet ──────────────────────────────────────────────────────────────
class PatientWalletView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = PatientPortalProfile.objects.filter(user_id=request.user.id).first()
        if not profile:
            return Response({"detail": "No profile"}, status=404)
        wallet, _ = PatientWallet.objects.get_or_create(profile=profile)
        return Response(PatientWalletSerializer(wallet).data)


# ── Insurance ───────────────────────────────────────────────────────────
class InsurancePolicyViewSet(viewsets.ModelViewSet):
    queryset = InsurancePolicy.objects.filter(is_deleted=False)
    serializer_class = InsurancePolicySerializer

    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        policy = self.get_object()
        # Placeholder: real verification via NPHIES / JoFotara on activation.
        policy.verified_at = timezone.now()
        nphies_insurers = {"BUPA", "TAWUNIYA", "MEDGULF", "WALAA", "MALATH", "ARABIA"}
        policy.verified_via = "nphies" if policy.insurer_code in nphies_insurers else "manual"
        policy.save(update_fields=["verified_at", "verified_via", "updated_at"])
        return Response(InsurancePolicySerializer(policy).data)

    @action(detail=True, methods=["post"], url_path="eligibility")
    def eligibility(self, request, pk=None):
        code = request.data.get("service_code")
        provider = request.data.get("provider_tenant_id")
        if not code:
            return Response({"detail": "service_code required"}, status=400)
        check = check_eligibility(pk, code, provider)
        return Response(EligibilityCheckSerializer(check).data)

    @action(detail=True, methods=["post"], url_path="preauth")
    def preauth(self, request, pk=None):
        code = request.data.get("service_code")
        provider = request.data.get("provider_tenant_id")
        justification = request.data.get("clinical_justification", "")
        if not (code and provider):
            return Response({"detail": "service_code + provider_tenant_id required"}, status=400)
        pa = submit_preauth(pk, code, justification, provider)
        return Response(PreAuthorizationSerializer(pa).data, status=202)


class PreAuthorizationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PreAuthorization.objects.all()
    serializer_class = PreAuthorizationSerializer
