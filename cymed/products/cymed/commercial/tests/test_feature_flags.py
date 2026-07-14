"""
Tests for CyMed Commercial — Feature Flag Framework.
Covers: models, service evaluation, tenant overrides, customer overrides, caching.
"""

import uuid
from unittest.mock import patch

import pytest

from products.cymed.commercial.feature_flags.models import (
    CustomerFeature,
    FeatureDependency,
    FeatureFlag,
    TenantFeature,
)
from products.cymed.commercial.feature_flags.services import FeatureFlagService

TENANT = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000001")
CUSTOMER_ID = uuid.UUID("cccccccc-0000-0000-0000-000000000001")
PLATFORM_TENANT = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def flag(db):
    obj, _ = FeatureFlag.objects.get_or_create(
        code="clinic.appointments",
        defaults={
            "tenant_id": PLATFORM_TENANT,
            "name": "Appointments",
            "scope": "edition",
            "default_enabled": True,
        },
    )
    return obj


@pytest.fixture
def flag_disabled(db):
    obj, _ = FeatureFlag.objects.get_or_create(
        code="clinic.icu",
        defaults={
            "tenant_id": PLATFORM_TENANT,
            "name": "ICU",
            "scope": "edition",
            "default_enabled": False,
        },
    )
    return obj


@pytest.fixture
def tenant_override_enabled(db, flag_disabled):
    return TenantFeature.objects.create(
        tenant_id=TENANT,
        feature=flag_disabled,
        is_enabled=True,
        override_reason="enterprise_upgrade",
    )


@pytest.fixture
def customer_override_enabled(db, flag_disabled):
    return CustomerFeature.objects.create(
        tenant_id=PLATFORM_TENANT,
        customer_id=CUSTOMER_ID,
        feature=flag_disabled,
        is_enabled=True,
    )


class TestFeatureFlagModel:
    def test_str(self, flag):
        assert str(flag) == "clinic.appointments"

    def test_unique_code(self, db, flag):
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            FeatureFlag.objects.create(
                tenant_id=PLATFORM_TENANT, code="clinic.appointments", name="Dup"
            )


class TestFeatureFlagService:
    @patch("products.cymed.commercial.feature_flags.services.cache")
    def test_is_enabled_default_true(self, mock_cache, flag):
        mock_cache.get.return_value = None
        result = FeatureFlagService.is_enabled("clinic.appointments")
        assert result is True

    @patch("products.cymed.commercial.feature_flags.services.cache")
    def test_is_enabled_default_false(self, mock_cache, flag_disabled):
        mock_cache.get.return_value = None
        result = FeatureFlagService.is_enabled("clinic.icu")
        assert result is False

    @patch("products.cymed.commercial.feature_flags.services.cache")
    def test_tenant_override_enables_disabled_flag(
        self, mock_cache, tenant_override_enabled, flag_disabled
    ):
        mock_cache.get.return_value = None
        result = FeatureFlagService.is_enabled("clinic.icu", tenant_id=str(TENANT))
        assert result is True

    @patch("products.cymed.commercial.feature_flags.services.cache")
    def test_customer_override_enables_disabled_flag(
        self, mock_cache, customer_override_enabled, flag_disabled
    ):
        mock_cache.get.return_value = None
        result = FeatureFlagService.is_enabled("clinic.icu", customer_id=str(CUSTOMER_ID))
        assert result is True

    @patch("products.cymed.commercial.feature_flags.services.cache")
    def test_nonexistent_flag_returns_false(self, mock_cache, db):
        mock_cache.get.return_value = None
        result = FeatureFlagService.is_enabled("nonexistent.flag")
        assert result is False

    @patch("products.cymed.commercial.feature_flags.services.cache")
    def test_get_tenant_feature_map(self, mock_cache, flag, flag_disabled, tenant_override_enabled):
        mock_cache.get.return_value = None
        fmap = FeatureFlagService.get_tenant_feature_map(str(TENANT))
        assert fmap["clinic.appointments"] is True
        assert fmap["clinic.icu"] is True  # overridden

    @patch("products.cymed.commercial.feature_flags.services.cache")
    def test_bulk_enable_edition_features(self, mock_cache, flag, flag_disabled):
        mock_cache.get.return_value = None
        count = FeatureFlagService.bulk_enable_edition_features(
            str(TENANT), ["clinic.appointments", "clinic.icu"]
        )
        assert count == 2
        assert TenantFeature.objects.filter(tenant_id=TENANT).count() >= 2

    @patch("products.cymed.commercial.feature_flags.services.cache")
    def test_cache_hit_returns_cached_value(self, mock_cache, flag):
        mock_cache.get.return_value = False
        result = FeatureFlagService.is_enabled("clinic.appointments", tenant_id=str(TENANT))
        assert result is False  # from cache, not default


class TestFeatureDependency:
    def test_dependency_created(self, db, flag, flag_disabled):
        dep = FeatureDependency.objects.create(
            tenant_id=PLATFORM_TENANT,
            feature=flag,
            requires_feature_code="clinic.icu",
        )
        assert dep.feature == flag
        assert dep.requires_feature_code == "clinic.icu"
