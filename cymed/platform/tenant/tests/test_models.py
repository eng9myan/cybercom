"""Tests for Tenant model."""

import pytest

from platform.tenant.models import TenantStatus, TenantTier


@pytest.mark.unit
class TestTenantModel:
    def test_tenant_status_choices(self):
        assert TenantStatus.ACTIVE == "active"
        assert TenantStatus.SUSPENDED == "suspended"

    def test_tenant_tier_choices(self):
        assert TenantTier.SHARED == "shared"
        assert TenantTier.CLUSTER == "cluster"
