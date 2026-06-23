"""
Feature Flag Service — central evaluation engine for edition/country/tenant/customer feature access.
No hardcoded feature access anywhere in CyMed — all checks flow through this service.
"""
from typing import Optional
import uuid

from django.core.cache import cache

from products.cymed.commercial.feature_flags.models import (
    FeatureFlag, TenantFeature, CustomerFeature
)


CACHE_TTL = 300  # 5 minutes


class FeatureFlagService:

    @staticmethod
    def _cache_key(scope: str, identifier: str, feature_code: str) -> str:
        return f"cymed:feature:{scope}:{identifier}:{feature_code}"

    @classmethod
    def is_enabled(
        cls,
        feature_code: str,
        tenant_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> bool:
        """
        Evaluation order:
        1. Customer-level override
        2. Tenant-level override
        3. Feature default_enabled
        """
        try:
            flag = FeatureFlag.objects.get(code=feature_code)
        except FeatureFlag.DoesNotExist:
            return False

        # Customer override (highest priority)
        if customer_id:
            cache_key = cls._cache_key("customer", str(customer_id), feature_code)
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            override = CustomerFeature.objects.filter(
                customer_id=customer_id, feature=flag
            ).first()
            if override is not None:
                cache.set(cache_key, override.is_enabled, CACHE_TTL)
                return override.is_enabled

        # Tenant override
        if tenant_id:
            cache_key = cls._cache_key("tenant", str(tenant_id), feature_code)
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            override = TenantFeature.objects.filter(
                tenant_id=tenant_id, feature=flag
            ).first()
            if override is not None:
                cache.set(cache_key, override.is_enabled, CACHE_TTL)
                return override.is_enabled

        return flag.default_enabled

    @classmethod
    def get_tenant_feature_map(cls, tenant_id: str) -> dict:
        """Return dict of {feature_code: bool} for all flags applicable to tenant."""
        flags = FeatureFlag.objects.all()
        result = {}
        overrides = {
            tf.feature_id: tf.is_enabled
            for tf in TenantFeature.objects.filter(tenant_id=tenant_id)
        }
        for flag in flags:
            result[flag.code] = overrides.get(flag.id, flag.default_enabled)
        return result

    @classmethod
    def invalidate_tenant_cache(cls, tenant_id: str) -> None:
        """Invalidate all feature flag cache entries for a tenant (called on override change)."""
        pattern = f"cymed:feature:tenant:{tenant_id}:*"
        cache.delete_pattern(pattern)

    @classmethod
    def bulk_enable_edition_features(
        cls,
        tenant_id: str,
        feature_codes: list,
    ) -> int:
        """Enable a list of feature codes for a tenant (used during edition provisioning)."""
        count = 0
        for code in feature_codes:
            try:
                flag = FeatureFlag.objects.get(code=code)
            except FeatureFlag.DoesNotExist:
                continue
            TenantFeature.objects.update_or_create(
                tenant_id=tenant_id,
                feature=flag,
                defaults={"is_enabled": True, "override_reason": "edition_provisioning"},
            )
            count += 1
        return count


# Edition → feature code mapping
CLINIC_STARTER_FEATURES = [
    "clinic.appointments",
    "clinic.reception",
    "clinic.queue",
    "clinic.consultation",
    "clinic.telemedicine",
]

CLINIC_PROFESSIONAL_FEATURES = CLINIC_STARTER_FEATURES + [
    "clinic.specialty_templates",
    "clinic.advanced_scheduling",
    "clinic.referral_management",
    "clinic.insurance_verification",
]

CLINIC_ENTERPRISE_FEATURES = CLINIC_PROFESSIONAL_FEATURES + [
    "clinic.multi_clinic",
    "clinic.enterprise_reporting",
    "clinic.advanced_workforce",
    "clinic.advanced_analytics",
    "clinic.multi_organization",
]

HOSPITAL_COMMUNITY_FEATURES = [
    "hospital.adt",
    "hospital.bed_management",
    "hospital.emergency",
    "hospital.inpatient",
    "hospital.nursing",
    "hospital.discharge",
]

HOSPITAL_ENTERPRISE_FEATURES = HOSPITAL_COMMUNITY_FEATURES + [
    "hospital.icu",
    "hospital.operating_room",
    "hospital.anesthesia",
    "hospital.maternity",
    "hospital.transfer_center",
    "hospital.capacity_management",
]

HOSPITAL_MEDICAL_CITY_FEATURES = HOSPITAL_ENTERPRISE_FEATURES + [
    "hospital.clinical_command_center",
    "hospital.multi_hospital",
    "hospital.academic_center",
    "hospital.regional_network",
]

# Laboratory Edition Feature Maps (Program 3.3)
LAB_BASIC_FEATURES = [
    "lab.orders",
    "lab.specimens",
    "lab.accessioning",
    "lab.worklists",
    "lab.results",
    "lab.blood_bank",
]

LAB_ADVANCED_FEATURES = LAB_BASIC_FEATURES + [
    "lab.microbiology",
    "lab.pathology",
    "lab.histopathology",
    "lab.quality",
    "lab.analytics",
]

LAB_REFERENCE_FEATURES = LAB_ADVANCED_FEATURES + [
    "lab.reference_lab",
    "lab.multi_site",
    "lab.cross_lab_routing",
]

LAB_NATIONAL_FEATURES = LAB_REFERENCE_FEATURES + [
    "lab.public_health",
    "lab.national_registry",
    "lab.population_analytics",
    "lab.government_integration",
]

# Imaging Edition Feature Maps (Program 3.4)
IMAGING_BASIC_FEATURES = [
    "imaging.orders",
    "imaging.scheduling",
    "imaging.reporting",
    "imaging.results",
]

IMAGING_ENTERPRISE_FEATURES = IMAGING_BASIC_FEATURES + [
    "imaging.pacs",
    "imaging.dicom",
    "imaging.worklist",
    "imaging.quality",
    "imaging.analytics",
]

IMAGING_TELERADIOLOGY_FEATURES = IMAGING_ENTERPRISE_FEATURES + [
    "imaging.teleradiology",
    "imaging.second_opinion",
    "imaging.multi_site",
    "imaging.reading_network",
]

IMAGING_NATIONAL_FEATURES = IMAGING_TELERADIOLOGY_FEATURES + [
    "imaging.national_registry",
    "imaging.government",
    "imaging.population_analytics",
    "imaging.public_health_reporting",
]

EDITION_FEATURE_MAP = {
    "cymed_clinic:starter": CLINIC_STARTER_FEATURES,
    "cymed_clinic:professional": CLINIC_PROFESSIONAL_FEATURES,
    "cymed_clinic:enterprise": CLINIC_ENTERPRISE_FEATURES,
    "cymed_hospital:community": HOSPITAL_COMMUNITY_FEATURES,
    "cymed_hospital:enterprise": HOSPITAL_ENTERPRISE_FEATURES,
    "cymed_hospital:medical_city": HOSPITAL_MEDICAL_CITY_FEATURES,
    "cymed_laboratory:basic": LAB_BASIC_FEATURES,
    "cymed_laboratory:advanced": LAB_ADVANCED_FEATURES,
    "cymed_laboratory:reference": LAB_REFERENCE_FEATURES,
    "cymed_laboratory:national": LAB_NATIONAL_FEATURES,
    "cymed_imaging:basic": IMAGING_BASIC_FEATURES,
    "cymed_imaging:enterprise": IMAGING_ENTERPRISE_FEATURES,
    "cymed_imaging:teleradiology": IMAGING_TELERADIOLOGY_FEATURES,
    "cymed_imaging:national": IMAGING_NATIONAL_FEATURES,
}
