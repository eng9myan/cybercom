"""
Real company profile + integration status for the Settings overview page
(which used to show a hard-coded "Cycom Co." / JOD / "Healthy" mock).

Every value is read from where the platform actually keeps it: the tenant
and its profile, the provisioning country pack (currency), and each
integration's own configuration check. "Configured" means credentials are
present -- it is never a claim that a remote service is reachable.
"""
from __future__ import annotations

import json
import os

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims

_PACKS = os.path.join(settings.BASE_DIR.parent, "platform", "provisioning", "packs", "countries")


def _country_currency(code: str) -> str:
    try:
        with open(os.path.join(_PACKS, f"{code.upper()}.json"), encoding="utf-8") as fh:
            return json.load(fh).get("currency", "")
    except (OSError, ValueError):
        return ""


def _integrations(tenant_id, country: str) -> list[dict]:
    from platform.einvoicing.engine import NATIONAL_FORMATS, mode_for_country

    out = []
    mode = mode_for_country(country)
    fmt = NATIONAL_FORMATS.get(mode or "")
    if fmt:
        out.append({"key": "einvoicing", "detail": fmt.label,
                    "status": "configured" if getattr(fmt.client(), "configured", False) else "manual"})
    elif mode:
        out.append({"key": "einvoicing", "detail": mode, "status": "configured"})
    else:
        out.append({"key": "einvoicing", "detail": "", "status": "not_applicable"})

    hyperpay = bool(getattr(settings, "HYPERPAY_ENTITY_ID", "") and getattr(settings, "HYPERPAY_ACCESS_TOKEN", ""))
    out.append({"key": "payments", "detail": (getattr(settings, "HYPERPAY_ENV", "test") or "test") if hyperpay else "",
                "status": "configured" if hyperpay else "not_configured"})

    backend = getattr(settings, "EMAIL_BACKEND", "")
    real_mail = backend and not backend.endswith(("console.EmailBackend", "locmem.EmailBackend", "dummy.EmailBackend"))
    out.append({"key": "email", "detail": backend.rsplit(".", 2)[-2] if backend else "",
                "status": "configured" if real_mail else "not_configured"})

    sms = getattr(settings, "SMS_BACKEND", "") or ""
    out.append({"key": "sms", "detail": "", "status": "configured" if sms and "Console" not in sms else "not_configured"})

    out.append({"key": "ai_documents", "detail": "",
                "status": "configured" if os.getenv("ANTHROPIC_API_KEY") else "not_configured"})

    if country == "GB":
        from platform.einvoicing.models import HmrcMtdConnection
        from platform.einvoicing.periodic.mtd_vat import HmrcMtdClient

        connected = HmrcMtdConnection.objects.filter(tenant_id=tenant_id).exists()
        out.append({"key": "hmrc_mtd", "detail": "",
                    "status": "connected" if connected else
                    ("configured" if HmrcMtdClient().configured else "not_configured")})
    return out


class SystemStatusView(APIView):
    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        from platform.einvoicing.models import EInvoiceProfile
        from platform.tenant.models import Tenant, TenantProfile

        tenant = Tenant.objects.filter(id=request.tenant_id).first()
        profile = TenantProfile.objects.filter(tenant_id=request.tenant_id).first()
        ep = EInvoiceProfile.objects.filter(tenant_id=request.tenant_id).first()
        country = (getattr(tenant, "country_code", "") or "").upper()
        return Response({
            "company": {
                "name": (getattr(profile, "legal_name", "") or getattr(tenant, "display_name", "")
                         or getattr(tenant, "name", "")),
                "tax_id": (ep.tax_id if ep and ep.tax_id else getattr(profile, "vat_number", "")) or "",
                "country_code": country,
                "currency": _country_currency(country) if country else "",
                "timezone": getattr(tenant, "timezone", ""),
                "locale": getattr(tenant, "locale", ""),
                "status": getattr(tenant, "status", ""),
            },
            "integrations": _integrations(request.tenant_id, country),
        })
