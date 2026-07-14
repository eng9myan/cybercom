"""
Tests for Program 3.C0 Retrofit — Clinic Edition and Hospital Edition commercial integration.
Verifies that edition-aware base views enforce feature gates correctly.
"""

import uuid
from unittest.mock import MagicMock, patch

from products.cymed.commercial.feature_flags.services import EDITION_FEATURE_MAP, FeatureFlagService


class TestClinicEditionFeatureMap:
    def test_starter_has_appointments(self):
        features = EDITION_FEATURE_MAP["cymed_clinic:starter"]
        assert "clinic.appointments" in features

    def test_starter_does_not_have_multi_clinic(self):
        features = EDITION_FEATURE_MAP["cymed_clinic:starter"]
        assert "clinic.multi_clinic" not in features

    def test_professional_has_referrals(self):
        features = EDITION_FEATURE_MAP["cymed_clinic:professional"]
        assert "clinic.referral_management" in features

    def test_enterprise_is_superset_of_professional(self):
        prof = set(EDITION_FEATURE_MAP["cymed_clinic:professional"])
        ent = set(EDITION_FEATURE_MAP["cymed_clinic:enterprise"])
        assert prof.issubset(ent)


class TestHospitalEditionFeatureMap:
    def test_community_has_adt(self):
        features = EDITION_FEATURE_MAP["cymed_hospital:community"]
        assert "hospital.adt" in features

    def test_community_does_not_have_icu(self):
        features = EDITION_FEATURE_MAP["cymed_hospital:community"]
        assert "hospital.icu" not in features

    def test_enterprise_has_icu(self):
        features = EDITION_FEATURE_MAP["cymed_hospital:enterprise"]
        assert "hospital.icu" in features

    def test_enterprise_has_operating_room(self):
        features = EDITION_FEATURE_MAP["cymed_hospital:enterprise"]
        assert "hospital.operating_room" in features

    def test_medical_city_has_command_center(self):
        features = EDITION_FEATURE_MAP["cymed_hospital:medical_city"]
        assert "hospital.clinical_command_center" in features

    def test_medical_city_is_superset_of_enterprise(self):
        ent = set(EDITION_FEATURE_MAP["cymed_hospital:enterprise"])
        mc = set(EDITION_FEATURE_MAP["cymed_hospital:medical_city"])
        assert ent.issubset(mc)


class TestClinicViewEditionGate:
    @patch("products.cymed.commercial.feature_flags.services.FeatureFlag.objects.get")
    @patch("products.cymed.commercial.feature_flags.services.TenantFeature.objects.filter")
    @patch("products.cymed.commercial.feature_flags.services.cache")
    def test_feature_gate_blocks_when_disabled(self, mock_cache, mock_tf_filter, mock_flag_get):
        mock_cache.get.return_value = None
        mock_flag = MagicMock()
        mock_flag.default_enabled = False
        mock_flag_get.return_value = mock_flag
        mock_tf_filter.return_value.first.return_value = None

        enabled = FeatureFlagService.is_enabled(
            "clinic.multi_clinic",
            tenant_id=str(uuid.uuid4()),
        )
        assert enabled is False

    @patch("products.cymed.commercial.feature_flags.services.FeatureFlag.objects.get")
    @patch("products.cymed.commercial.feature_flags.services.TenantFeature.objects.filter")
    @patch("products.cymed.commercial.feature_flags.services.cache")
    def test_feature_gate_passes_when_enabled(self, mock_cache, mock_tf_filter, mock_flag_get):
        mock_cache.get.return_value = None
        mock_flag = MagicMock()
        mock_flag.default_enabled = True
        mock_flag_get.return_value = mock_flag
        mock_tf_filter.return_value.first.return_value = None

        enabled = FeatureFlagService.is_enabled(
            "clinic.appointments",
            tenant_id=str(uuid.uuid4()),
        )
        assert enabled is True


class TestBulkEditionProvisioning:
    @patch("products.cymed.commercial.feature_flags.services.cache")
    def test_bulk_enable_clinic_starter(self, mock_cache, db):
        from products.cymed.commercial.feature_flags.models import FeatureFlag, TenantFeature

        PLATFORM_TENANT = uuid.UUID("00000000-0000-0000-0000-000000000001")
        tenant_id = str(uuid.uuid4())

        features_to_create = EDITION_FEATURE_MAP["cymed_clinic:starter"]
        for code in features_to_create:
            FeatureFlag.objects.get_or_create(
                code=code,
                defaults={
                    "tenant_id": PLATFORM_TENANT,
                    "name": code,
                    "scope": "edition",
                    "default_enabled": False,
                },
            )

        mock_cache.get.return_value = None
        count = FeatureFlagService.bulk_enable_edition_features(tenant_id, features_to_create)
        assert count == len(features_to_create)
        assert TenantFeature.objects.filter(tenant_id=tenant_id).count() == len(features_to_create)
