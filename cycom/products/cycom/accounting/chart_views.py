"""Seed the tenant's chart of accounts from its country pack."""
from __future__ import annotations

import json
import os
from types import SimpleNamespace

from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from platform.provisioning.models import CountryPack
from platform.provisioning.services import seed_chart_of_accounts
from platform.tenant.models import Tenant
from products.cycom.accounting.sequencing import OVERRIDE_ROLES


def _country_pack(code: str):
    pack = CountryPack.objects.filter(code=code, is_active=True).order_by("-version").first()
    if pack is not None:
        return pack
    # Catalogue not seeded into the DB yet: the vendored JSON is the source.
    path = os.path.join(settings.ROOT_DIR, "platform", "provisioning", "packs", "countries", f"{code}.json")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return SimpleNamespace(coa_template=data.get("coa_template", []), currency=data.get("currency", ""),
                           default_locale=data.get("default_locale", "en"))


class SeedChartView(APIView):
    """POST: create every account of the country chart that the tenant
    doesn't have yet (existing accounts are never changed)."""

    permission_classes = [IsAuthenticatedViaClaims]

    def post(self, request):
        session = getattr(request, "user_session", None) or {}
        claims = getattr(request, "auth_claims", None) or {}
        roles = set(session.get("roles", [])) | set(claims.get("realm_access", {}).get("roles", []))
        if not roles & OVERRIDE_ROLES:
            raise PermissionDenied("Creating the chart of accounts requires a finance or admin role.")
        tenant = Tenant.objects.filter(id=request.tenant_id).first()
        code = str(request.data.get("country_code") or getattr(tenant, "country_code", "") or "").upper()
        pack = _country_pack(code) if code else None
        if pack is None:
            return Response({"detail": f"No chart-of-accounts template for country '{code}'."}, status=400)
        result = seed_chart_of_accounts(request.tenant_id, pack, locale=getattr(tenant, "locale", None))
        return Response({"country_code": code, **result})
