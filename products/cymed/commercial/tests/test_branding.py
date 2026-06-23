"""
Tests for CyMed Commercial — White Label Branding Platform.
"""
import uuid
import pytest

from products.cymed.commercial.branding.models import (
    Brand, BrandTheme, BrandAsset, BrandDomain, BrandLocalization
)
from products.cymed.commercial.branding.services import BrandingService

TENANT = uuid.UUID("ffffffff-0000-0000-0000-000000000001")


@pytest.fixture
def brand(db):
    return Brand.objects.create(
        tenant_id=TENANT,
        code="seha_jordan",
        name="Seha Jordan",
        is_default=False,
        is_active=True,
    )


@pytest.fixture
def brand_with_theme(db, brand):
    BrandTheme.objects.create(
        tenant_id=TENANT,
        brand=brand,
        primary_color="#005A9C",
        secondary_color="#004A7C",
        heading_font="Cairo",
        body_font="Cairo",
    )
    return brand


@pytest.fixture
def brand_with_domain(db, brand):
    BrandDomain.objects.create(
        tenant_id=TENANT,
        brand=brand,
        domain="clinic.seha.jo",
        is_primary=True,
    )
    return brand


@pytest.fixture
def brand_with_localization(db, brand):
    BrandLocalization.objects.create(
        tenant_id=TENANT,
        brand=brand,
        language_code="ar",
        app_name="صحة",
        tagline="رعاية صحية متميزة",
        login_title="تسجيل الدخول",
        is_rtl=True,
    )
    BrandLocalization.objects.create(
        tenant_id=TENANT,
        brand=brand,
        language_code="en",
        app_name="Seha",
        tagline="Excellence in Healthcare",
        login_title="Sign In",
        is_rtl=False,
    )
    return brand


class TestBrandModel:
    def test_str(self, brand):
        assert str(brand) == "Seha Jordan"

    def test_unique_code(self, db, brand):
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Brand.objects.create(tenant_id=TENANT, code="seha_jordan", name="Dup")


class TestBrandingService:
    def test_get_brand_for_domain(self, brand_with_domain):
        found = BrandingService.get_brand_for_domain("clinic.seha.jo")
        assert found is not None
        assert found.code == "seha_jordan"

    def test_get_brand_for_unknown_domain(self, db):
        result = BrandingService.get_brand_for_domain("unknown.example.com")
        assert result is None

    def test_get_brand_theme(self, brand_with_theme):
        theme = BrandingService.get_brand_theme(brand_with_theme)
        assert theme is not None
        assert theme["primary_color"] == "#005A9C"
        assert theme["heading_font"] == "Cairo"

    def test_get_localization_arabic(self, brand_with_localization):
        loc = BrandingService.get_localization(brand_with_localization, "ar")
        assert loc["is_rtl"] is True
        assert loc["app_name"] == "صحة"

    def test_get_localization_english(self, brand_with_localization):
        loc = BrandingService.get_localization(brand_with_localization, "en")
        assert loc["is_rtl"] is False
        assert loc["app_name"] == "Seha"

    def test_get_full_brand_config(self, brand_with_theme, brand_with_localization):
        brand = brand_with_theme
        config = BrandingService.get_full_brand_config(brand, "en")
        assert config["brand_code"] == "seha_jordan"
        assert config["theme"]["primary_color"] == "#005A9C"
        assert config["localization"]["app_name"] == "Seha"


class TestBrandAsset:
    def test_create_asset(self, db, brand):
        asset = BrandAsset.objects.create(
            tenant_id=TENANT,
            brand=brand,
            asset_type="logo_light",
            asset_url="https://cdn.seha.jo/logo-light.svg",
            language_code="en",
        )
        assert asset.asset_type == "logo_light"

    def test_unique_asset_type_language(self, db, brand):
        from django.db import IntegrityError
        BrandAsset.objects.create(
            tenant_id=TENANT, brand=brand, asset_type="logo_light",
            asset_url="https://cdn.seha.jo/a.svg", language_code="en"
        )
        with pytest.raises(IntegrityError):
            BrandAsset.objects.create(
                tenant_id=TENANT, brand=brand, asset_type="logo_light",
                asset_url="https://cdn.seha.jo/b.svg", language_code="en"
            )
