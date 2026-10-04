"""
Platform-wide fleet KPI dashboard — Phase 4 (Odoo.sh-equivalent hosting),
item 3. The existing SystemStatusView (cycom/core/views/system_status.py)
is deliberately per-tenant (a signed-in tenant's own Settings page); this
is the operator-facing counterpart, aggregating across every tenant —
exactly the "monitoring/KPI dashboard" Odoo.sh itself provides for an
implementer managing many customer instances. platform_admin only.
"""
from __future__ import annotations

from collections import Counter

from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from platform.api.permissions import _roles
from platform.ephemeral_envs.models import EphemeralEnvironment
from platform.tenant.models import Tenant, TenantStatus, TenantSubscription


class IsPlatformAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        return "platform_admin" in _roles(request)


class PlatformKpiDashboardView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        from platform.einvoicing.engine import mode_for_country

        tenants = Tenant.objects.all()
        tenant_counts = Counter(tenants.values_list("status", flat=True))

        einvoicing_counts: Counter = Counter()
        for country in tenants.values_list("country_code", flat=True):
            mode = mode_for_country((country or "").upper()) or "none"
            einvoicing_counts[mode] += 1

        active_subs = TenantSubscription.objects.filter(is_active=True)
        plan_counts = Counter(active_subs.values_list("plan", flat=True))

        env_counts = Counter(EphemeralEnvironment.objects.values_list("status", flat=True))

        return Response({
            "tenants": {
                "total": tenants.count(),
                "by_status": {s.value: tenant_counts.get(s.value, 0) for s in TenantStatus},
            },
            "active_subscriptions_by_plan": dict(plan_counts),
            "einvoicing_coverage": dict(einvoicing_counts),
            "ephemeral_environments": {
                "total": sum(env_counts.values()),
                "by_status": dict(env_counts),
            },
        })
