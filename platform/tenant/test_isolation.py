"""Regression: tenant sub-resource viewsets must not leak cross-tenant rows.

Security review Finding (cross-tenant read): TenantSubscriptionViewSet etc.
were plain ModelViewSet with .objects.all() + ReadOnlyOrPlatformAdmin, so any
authenticated user could GET every tenant's rows. TenantScopedReadMixin scopes
reads to request.tenant_id; platform_admin (tenant_id None) still sees all.
"""

import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from platform.tenant.models import (
    SubscriptionPlan,
    Tenant,
    TenantSubscription,
    TenantType,
)
from platform.tenant.views import TenantSubscriptionViewSet, TenantViewSet


def _tenant(name):
    t = Tenant.objects.create(
        name=name, slug=name.lower(), tenant_type=TenantType.SAAS,
    )
    TenantSubscription.objects.create(tenant=t, plan=SubscriptionPlan.PROFESSIONAL)
    return t


def _req(tenant_id, roles=None):
    r = APIRequestFactory().get("/api/v1/tenants/subscriptions/")
    r.tenant_id = tenant_id
    r.auth_claims = {"sub": "u", "roles": roles or []}
    return r


class SubResourceIsolationTests(TestCase):
    def setUp(self):
        self.a = _tenant("AlphaCo")
        self.b = _tenant("BetaCo")

    def test_user_sees_only_own_tenant_subscriptions(self):
        view = TenantSubscriptionViewSet.as_view({"get": "list"})
        req = _req(self.a.id)
        # drive get_queryset directly for a precise isolation assertion
        vs = TenantSubscriptionViewSet()
        vs.request = req
        rows = list(vs.get_queryset())
        self.assertEqual({r.tenant_id for r in rows}, {self.a.id})
        self.assertNotIn(self.b.id, {r.tenant_id for r in rows})

    def test_platform_admin_sees_all(self):
        vs = TenantSubscriptionViewSet()
        vs.request = _req(None)  # platform_admin operates cross-tenant
        rows = list(vs.get_queryset())
        self.assertEqual({r.tenant_id for r in rows}, {self.a.id, self.b.id})

    def test_tenant_list_scoped_to_own(self):
        vs = TenantViewSet()
        vs.request = _req(self.a.id)
        ids = {t.id for t in vs.get_queryset()}
        self.assertEqual(ids, {self.a.id})
