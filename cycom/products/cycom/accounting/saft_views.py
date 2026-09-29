"""SAF-T (Norway) settings/mapping + export endpoints."""
from __future__ import annotations

from datetime import date

from django.http import HttpResponse
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from platform.einvoicing.models import EInvoiceProfile
from platform.einvoicing.national import EInvoiceDataMissing
from platform.einvoicing.periodic.saft_no import (
    PURCHASE_ZERO_CODES,
    SALES_ZERO_CODES,
    build_saft_no,
    grouping_codes,
    schema_errors,
    standard_tax_codes,
)
from products.cycom.accounting.models import Account
from products.cycom.accounting.saft import SAFT_ATTR, SETTING_KEYS, collect
from products.cycom.accounting.sequencing import OVERRIDE_ROLES


def _require_finance_role(request):
    session = getattr(request, "user_session", None) or {}
    roles = set(session.get("roles", []))
    claims = getattr(request, "auth_claims", None) or {}
    roles |= set(claims.get("realm_access", {}).get("roles", []))
    if not roles & OVERRIDE_ROLES:
        raise PermissionDenied("Changing SAF-T settings requires a finance or admin role.")


def _parse_date(value, field):
    try:
        return date.fromisoformat(value), None
    except (TypeError, ValueError):
        return None, {"detail": f"'{field}' must be a YYYY-MM-DD date."}


class SaftSettingsView(APIView):
    """GET: accounts with their current grouping mapping, the official
    grouping list, and tenant SAF-T settings. PATCH: save mappings/settings
    (every grouping pair is checked against the official list)."""

    permission_classes = [IsAuthenticatedViaClaims]

    def _payload(self, tenant_id):
        ep = EInvoiceProfile.objects.filter(tenant_id=tenant_id).first()
        national = (ep.national if ep else {}) or {}
        codes = grouping_codes()
        std = standard_tax_codes()
        return {
            "accounts": [
                {"id": str(a.id), "code": a.code, "name": a.name, "account_type": a.account_type,
                 "grouping_category": (a.attributes or {}).get(SAFT_ATTR, {}).get("grouping_category", ""),
                 "grouping_code": (a.attributes or {}).get(SAFT_ATTR, {}).get("grouping_code", "")}
                for a in Account.objects.filter(tenant_id=tenant_id, is_postable=True).order_by("code")
            ],
            "grouping": [
                {"category": cat, "codes": [{"code": c, "description": d} for c, d in sorted(items.items())]}
                for cat, items in sorted(codes.items())
            ],
            "settings": {k: national.get(k, "") for k in SETTING_KEYS},
            "sales_zero_codes": [{"code": c, "description": std.get(c, "")} for c in SALES_ZERO_CODES],
            "purchase_zero_codes": [{"code": c, "description": std.get(c, "")} for c in PURCHASE_ZERO_CODES],
        }

    def get(self, request):
        return Response(self._payload(request.tenant_id))

    def patch(self, request):
        _require_finance_role(request)
        tenant_id = request.tenant_id
        codes = grouping_codes()
        errors = []
        updates = []
        for acc_id, m in (request.data.get("accounts") or {}).items():
            acc = Account.objects.filter(tenant_id=tenant_id, id=acc_id).first() if _is_uuid(acc_id) else None
            if acc is None:
                errors.append({"key": str(acc_id), "message": "not an account of this company"})
                continue
            cat, code = (m.get("grouping_category") or "").strip(), (m.get("grouping_code") or "").strip()
            if (cat or code) and code not in codes.get(cat, {}):
                errors.append({"key": acc.code, "message": f"'{cat}/{code}' is not an official grouping code"})
                continue
            updates.append((acc, cat, code))
        settings_in = request.data.get("settings") or {}
        if settings_in.get("saft_sales_zero_code") not in (None, "", *SALES_ZERO_CODES):
            errors.append({"key": "saft_sales_zero_code", "message": "not a sales 0% standard tax code"})
        if settings_in.get("saft_purchase_zero_code") not in (None, "", *PURCHASE_ZERO_CODES):
            errors.append({"key": "saft_purchase_zero_code", "message": "not a purchase 0% standard tax code"})
        if errors:
            return Response({"detail": "Some SAF-T settings are invalid.", "errors": errors}, status=400)

        for acc, cat, code in updates:
            attrs = dict(acc.attributes or {})
            if cat and code:
                attrs[SAFT_ATTR] = {"grouping_category": cat, "grouping_code": code}
            else:
                attrs.pop(SAFT_ATTR, None)
            acc.attributes = attrs
            acc.save(update_fields=["attributes", "updated_at"])
        if settings_in:
            ep, _ = EInvoiceProfile.objects.get_or_create(tenant_id=tenant_id)
            national = dict(ep.national or {})
            for k in SETTING_KEYS:
                if k in settings_in:
                    v = str(settings_in[k] or "").strip()
                    if v:
                        national[k] = v[:70]
                    else:
                        national.pop(k, None)
            ep.national = national
            ep.save(update_fields=["national", "updated_at"])
        return Response(self._payload(tenant_id))


class SaftExportView(APIView):
    """GET ?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD[&currency=NOK]: the
    audit file, or 400 with every missing mapping/setting listed."""

    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        date_from, err = _parse_date(request.query_params.get("date_from"), "date_from")
        if err:
            return Response(err, status=400)
        date_to, err = _parse_date(request.query_params.get("date_to"), "date_to")
        if err:
            return Response(err, status=400)
        if date_to < date_from:
            return Response({"detail": "date_to is before date_from."}, status=400)
        currency = (request.query_params.get("currency") or "NOK").upper()[:3]
        try:
            data = collect(request.tenant_id, date_from, date_to, currency)
        except EInvoiceDataMissing as exc:
            return Response({"detail": "The audit file can't be produced yet.", "problems": exc.problems}, status=400)
        xml = build_saft_no(data)
        errors = schema_errors(xml)
        if errors:
            return Response({"detail": "The generated file failed schema validation.", "schema_errors": errors[:20]},
                            status=500)
        filename = f"SAF-T Financial_{data.company.registration_number}_{date.today():%Y%m%d}.xml"
        resp = HttpResponse(xml, content_type="application/xml; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp


def _is_uuid(value) -> bool:
    import uuid

    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False
