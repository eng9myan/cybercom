"""
Tests for CyMed Commercial — Product Catalog.
"""

import uuid

import pytest

from products.cymed.commercial.product_catalog.models import (
    ProductFeatureMatrix,
    ProductLicenseMapping,
    ProductVersion,
)

TENANT = uuid.UUID("20000000-0000-0000-0000-000000000001")


@pytest.fixture
def product_version(db):
    return ProductVersion.objects.create(
        tenant_id=TENANT,
        product_code="cymed_clinic",
        version="1.0.0",
        release_date="2026-01-01",
        is_lts=True,
    )


@pytest.fixture
def license_mapping(db):
    return ProductLicenseMapping.objects.create(
        tenant_id=TENANT,
        product_code="cymed_clinic",
        edition_code="starter",
        license_types_allowed=["trial", "subscription", "annual"],
        delivery_modes_allowed=["online", "offline"],
        supports_white_label=True,
        supports_multi_tenant=False,
    )


@pytest.fixture
def feature_matrix(db):
    return ProductFeatureMatrix.objects.create(
        tenant_id=TENANT,
        product_code="cymed_clinic",
        edition_code="starter",
        feature_code="clinic.appointments",
        is_available=True,
        requires_addon=False,
    )


class TestProductVersion:
    def test_create(self, product_version):
        assert product_version.is_lts is True
        assert product_version.version == "1.0.0"

    def test_unique_product_version(self, db, product_version):
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            ProductVersion.objects.create(
                tenant_id=TENANT,
                product_code="cymed_clinic",
                version="1.0.0",
                release_date="2026-02-01",
            )


class TestProductLicenseMapping:
    def test_license_types(self, license_mapping):
        assert "trial" in license_mapping.license_types_allowed
        assert "subscription" in license_mapping.license_types_allowed

    def test_white_label_supported(self, license_mapping):
        assert license_mapping.supports_white_label is True

    def test_unique_product_edition(self, db, license_mapping):
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            ProductLicenseMapping.objects.create(
                tenant_id=TENANT,
                product_code="cymed_clinic",
                edition_code="starter",
            )


class TestProductFeatureMatrix:
    def test_feature_available(self, feature_matrix):
        assert feature_matrix.is_available is True
        assert feature_matrix.requires_addon is False

    def test_unique_product_edition_feature(self, db, feature_matrix):
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            ProductFeatureMatrix.objects.create(
                tenant_id=TENANT,
                product_code="cymed_clinic",
                edition_code="starter",
                feature_code="clinic.appointments",
            )
