"""UK MTD VAT: HMRC connection (OAuth2), obligations, 9-box preview, filing."""
from __future__ import annotations

import os
import re
from datetime import date, datetime, timedelta

from django.core import signing
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from platform.einvoicing.models import HmrcMtdConnection, MtdVatSubmission
from platform.einvoicing.national import EInvoiceDataMissing, TransportNotConfigured
from platform.einvoicing.periodic.mtd_vat import (
    VRN_RE,
    HmrcApiError,
    HmrcMtdClient,
    fraud_prevention_headers,
)
from products.cycom.accounting.mtd import compute_return
from products.cycom.accounting.sequencing import OVERRIDE_ROLES

STATE_SALT = "cycom.hmrc-mtd.oauth-state"
STATE_MAX_AGE = 900
DECLARATION = ("When you submit this VAT information you are making a legal declaration that the information "
               "is true and complete. A false declaration can result in prosecution.")


def vrn_valid(vrn: str) -> bool:
    """UK VAT registration number check digits (both mod-97 and mod-9755)."""
    if not re.fullmatch(VRN_RE, vrn or ""):
        return False
    total = sum(int(d) * w for d, w in zip(vrn[:7], range(8, 1, -1))) + int(vrn[7:])
    return total % 97 == 0 or (total + 55) % 97 == 0


def _roles(request) -> set:
    session = getattr(request, "user_session", None) or {}
    claims = getattr(request, "auth_claims", None) or {}
    return set(session.get("roles", [])) | set(claims.get("realm_access", {}).get("roles", []))


def _require_finance_role(request):
    if not _roles(request) & OVERRIDE_ROLES:
        raise PermissionDenied("VAT filing requires a finance or admin role.")


def _client() -> HmrcMtdClient:
    return HmrcMtdClient()


def _date(value, field):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"'{field}' must be a YYYY-MM-DD date.")


def _fraud(request, browser) -> dict:
    fwd = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip = (fwd.split(",")[0].strip() if fwd else request.META.get("REMOTE_ADDR", ""))
    claims = getattr(request, "auth_claims", None) or {}
    return fraud_prevention_headers(
        browser=browser or {}, client_ip=ip, user_id=str(claims.get("sub") or "unknown"),
        vendor_ip=os.getenv("HMRC_VENDOR_PUBLIC_IP", ""),
        client_port=request.META.get("HTTP_X_FORWARDED_PORT", ""),
    )


def _access_token(conn: HmrcMtdConnection, client: HmrcMtdClient) -> str:
    if conn.expires_at and conn.expires_at > timezone.now() + timedelta(seconds=60):
        return conn.access_token
    tok = client.refresh(conn.refresh_token)
    conn.access_token = tok["access_token"]
    conn.refresh_token = tok.get("refresh_token", conn.refresh_token)
    conn.expires_at = timezone.now() + timedelta(seconds=int(tok.get("expires_in", 14400)))
    conn.save(update_fields=["access_token", "refresh_token", "expires_at", "updated_at"])
    return conn.access_token


def _errors(fn):
    """Map the integration's failure modes to honest HTTP answers."""
    def wrapper(self, request, *a, **kw):
        try:
            return fn(self, request, *a, **kw)
        except TransportNotConfigured as exc:
            return Response({"detail": str(exc), "code": "not_configured"}, status=503)
        except HmrcApiError as exc:
            return Response({"detail": "HMRC rejected the request.", "hmrc_status": exc.status, "hmrc": exc.body},
                            status=502)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
    return wrapper


class MtdStatusView(APIView):
    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        client = _client()
        conn = HmrcMtdConnection.objects.filter(tenant_id=request.tenant_id).first()
        return Response({
            "configured": client.configured, "sandbox": client.sandbox,
            "connected": conn is not None, "vrn": conn.vrn if conn else "",
            "connected_at": conn.connected_at if conn else None, "declaration": DECLARATION,
        })


class MtdConnectView(APIView):
    """POST {vrn} -> HMRC authorise URL carrying a signed, tenant-bound state."""

    permission_classes = [IsAuthenticatedViaClaims]

    @_errors
    def post(self, request):
        _require_finance_role(request)
        vrn = re.sub(r"\D", "", str(request.data.get("vrn") or ""))
        if not vrn_valid(vrn):
            raise ValueError("Not a valid UK VAT registration number.")
        state = signing.dumps({"t": str(request.tenant_id), "v": vrn}, salt=STATE_SALT)
        return Response({"authorize_url": _client().authorize_url(state)})


class MtdCallbackView(APIView):
    """POST {code, state} from the page HMRC redirected back to."""

    permission_classes = [IsAuthenticatedViaClaims]

    @_errors
    def post(self, request):
        _require_finance_role(request)
        try:
            state = signing.loads(str(request.data.get("state") or ""), salt=STATE_SALT, max_age=STATE_MAX_AGE)
        except signing.BadSignature:
            raise ValueError("The HMRC authorisation link is invalid or expired; connect again.")
        if state.get("t") != str(request.tenant_id):
            raise ValueError("This HMRC authorisation belongs to a different company.")
        tok = _client().exchange_code(str(request.data.get("code") or ""))
        conn, _ = HmrcMtdConnection.objects.get_or_create(tenant_id=request.tenant_id, defaults={"vrn": state["v"]})
        conn.vrn = state["v"]
        conn.access_token = tok["access_token"]
        conn.refresh_token = tok.get("refresh_token", "")
        conn.expires_at = timezone.now() + timedelta(seconds=int(tok.get("expires_in", 14400)))
        conn.connected_at = timezone.now()
        conn.save()
        return MtdStatusView().get(request)


class MtdDisconnectView(APIView):
    permission_classes = [IsAuthenticatedViaClaims]

    def post(self, request):
        _require_finance_role(request)
        HmrcMtdConnection.objects.filter(tenant_id=request.tenant_id).delete()
        return Response(status=204)


class MtdObligationsView(APIView):
    """POST {browser} (fraud-prevention data from the page) -> open and
    fulfilled obligations for the last 12 months + the next 3."""

    permission_classes = [IsAuthenticatedViaClaims]

    @_errors
    def post(self, request):
        conn = HmrcMtdConnection.objects.filter(tenant_id=request.tenant_id).first()
        if conn is None:
            raise ValueError("Connect to HMRC first.")
        client = _client()
        today = date.today()
        obligations = client.obligations(conn.vrn, _access_token(conn, client), _fraud(request, request.data.get("browser")),
                                         today - timedelta(days=365), today + timedelta(days=90))
        filed = set(MtdVatSubmission.objects.filter(tenant_id=request.tenant_id, vrn=conn.vrn)
                    .values_list("period_key", flat=True))
        return Response([{**o, "filed_here": o.get("periodKey") in filed} for o in obligations])


class MtdPreviewView(APIView):
    permission_classes = [IsAuthenticatedViaClaims]

    @_errors
    def get(self, request):
        date_from = _date(request.query_params.get("date_from"), "date_from")
        date_to = _date(request.query_params.get("date_to"), "date_to")
        try:
            ret, meta = compute_return(request.tenant_id, date_from, date_to)
        except EInvoiceDataMissing as exc:
            return Response({"detail": "The return can't be computed from these records.", "problems": exc.problems},
                            status=400)
        return Response({"boxes": ret.as_boxes(), **meta})


class MtdSubmitView(APIView):
    """POST {period_key, date_from, date_to, declaration: true, browser}.
    Recomputes the boxes server-side (never trusts figures from the page),
    files them, and keeps the request + HMRC receipt permanently."""

    permission_classes = [IsAuthenticatedViaClaims]

    @_errors
    def post(self, request):
        _require_finance_role(request)
        if request.data.get("declaration") is not True:
            raise ValueError("The legal declaration must be confirmed before filing.")
        period_key = str(request.data.get("period_key") or "")
        if not re.fullmatch(r"[A-Z0-9#]{4}", period_key):
            raise ValueError("Invalid period key.")
        date_from = _date(request.data.get("date_from"), "date_from")
        date_to = _date(request.data.get("date_to"), "date_to")
        conn = HmrcMtdConnection.objects.filter(tenant_id=request.tenant_id).first()
        if conn is None:
            raise ValueError("Connect to HMRC first.")
        if MtdVatSubmission.objects.filter(tenant_id=request.tenant_id, vrn=conn.vrn, period_key=period_key).exists():
            return Response({"detail": "A return for this period was already filed from CyCom."}, status=409)
        try:
            ret, _meta = compute_return(request.tenant_id, date_from, date_to)
        except EInvoiceDataMissing as exc:
            return Response({"detail": "The return can't be computed from these records.", "problems": exc.problems},
                            status=400)
        body = ret.to_hmrc(period_key)
        client = _client()
        receipt = client.submit_return(conn.vrn, _access_token(conn, client),
                                       _fraud(request, request.data.get("browser")), body)
        claims = getattr(request, "auth_claims", None) or {}
        try:
            with transaction.atomic():
                sub = MtdVatSubmission.objects.create(
                    tenant_id=request.tenant_id, vrn=conn.vrn, period_key=period_key, date_from=date_from,
                    date_to=date_to, payload=body, receipt=receipt,
                    submitted_by=str(claims.get("email") or claims.get("sub") or ""))
        except IntegrityError:
            return Response({"detail": "A return for this period was already filed from CyCom."}, status=409)
        return Response(_submission(sub), status=201)


class MtdSubmissionsView(APIView):
    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        return Response([_submission(s) for s in MtdVatSubmission.objects.filter(tenant_id=request.tenant_id)])


def _submission(s: MtdVatSubmission) -> dict:
    return {"id": str(s.id), "vrn": s.vrn, "period_key": s.period_key, "date_from": s.date_from,
            "date_to": s.date_to, "payload": s.payload, "receipt": s.receipt, "submitted_by": s.submitted_by,
            "submitted_at": s.created_at}
