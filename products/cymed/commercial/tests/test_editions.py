"""
Tests for CyMed Commercial — Edition Management.
Covers: models, service, feature matrix, module access.
"""
import uuid
import pytest
from products.cymed.commercial.editions.models import (
    ProductCatalogEntry, ProductEdition, EditionFeature, EditionLimit, EditionModule
)
from products.cymed.commercial.editions.services import EditionService

TENANT = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def product(db):
    obj, _ = ProductCatalogEntry.objects.get_or_create(
        code="cymed_clinic",
        defaults={
            "tenant_id": TENANT,
            "name": "CyMed Clinic",
            "current_version": "1.0.0",
            "is_active": True,
        },
    )
    return obj


@pytest.fixture
def edition(db, product):
    obj, _ = ProductEdition.objects.get_or_create(
        product=product,
        code="starter",
        defaults={
            "tenant_id": TENANT,
            "name": "CyMed Clinic Starter",
            "tier": "starter",
            "max_users": 10,
            "max_providers": 5,
            "max_beds": 0,
            "max_facilities": 1,
            "max_clinics": 1,
            "sort_order": 1,
            "is_active": True,
        },
    )
    return obj


@pytest.fixture
def edition_with_features(db, edition):
    EditionFeature.objects.create(
        tenant_id=TENANT, edition=edition, feature_code="clinic.appointments", is_enabled=True
    )
    EditionFeature.objects.create(
        tenant_id=TENANT, edition=edition, feature_code="clinic.telemedicine", is_enabled=False
    )
    return edition


@pytest.fixture
def edition_with_modules(db, edition):
    EditionModule.objects.get_or_create(
        edition=edition, module_code="clinic.appointments",
        defaults={"tenant_id": TENANT, "is_included": True},
    )
    EditionModule.objects.get_or_create(
        edition=edition, module_code="clinic.icu",
        defaults={"tenant_id": TENANT, "is_included": False},
    )
    return edition


class TestProductCatalogEntry:
    def test_str(self, product):
        assert "cymed_clinic" in str(product)

    def test_unique_code(self, db, product):
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            ProductCatalogEntry.objects.create(
                tenant_id=TENANT, code="cymed_clinic", name="Duplicate"
            )


class TestProductEdition:
    def test_str(self, edition):
        assert "cymed_clinic:starter" in str(edition)

    def test_unique_product_code(self, db, product, edition):
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            ProductEdition.objects.create(
                tenant_id=TENANT, product=product, code="starter", name="Dup", tier="starter"
            )


class TestEditionService:
    def test_get_edition_found(self, edition):
        result = EditionService.get_edition("cymed_clinic", "starter")
        assert result is not None
        assert result.code == "starter"

    def test_get_edition_not_found(self, db):
        result = EditionService.get_edition("cymed_clinic", "nonexistent")
        assert result is None

    def test_get_edition_features(self, edition_with_features):
        features = EditionService.get_edition_features(edition_with_features)
        assert features["clinic.appointments"] is True
        assert features["clinic.telemedicine"] is False

    def test_get_edition_modules(self, edition_with_modules):
        modules = EditionService.get_edition_modules(edition_with_modules)
        assert "clinic.appointments" in modules
        assert "clinic.icu" not in modules

    def test_is_module_included_true(self, edition_with_modules):
        assert EditionService.is_module_included("cymed_clinic", "starter", "clinic.appointments") is True

    def test_is_module_included_false(self, edition_with_modules):
        assert EditionService.is_module_included("cymed_clinic", "starter", "clinic.icu") is False

    def test_within_user_limit(self, edition):
        assert EditionService.is_within_user_limit(edition, 5) is True
        assert EditionService.is_within_user_limit(edition, 10) is True
        assert EditionService.is_within_user_limit(edition, 11) is False

    def test_unlimited_user_limit(self, edition):
        edition.max_users = 0
        assert EditionService.is_within_user_limit(edition, 99999) is True

    def test_within_bed_limit_unlimited(self, edition):
        edition.max_beds = 0
        assert EditionService.is_within_bed_limit(edition, 99999) is True

    def test_within_bed_limit_bounded(self, edition):
        edition.max_beds = 100
        assert EditionService.is_within_bed_limit(edition, 100) is True
        assert EditionService.is_within_bed_limit(edition, 101) is False

    def test_get_edition_limits(self, db, edition):
        EditionLimit.objects.create(
            tenant_id=TENANT, edition=edition, resource_name="beds", max_value=100
        )
        limits = EditionService.get_edition_limits(edition)
        assert limits["beds"] == 100
