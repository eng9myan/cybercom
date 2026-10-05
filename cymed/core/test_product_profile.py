"""
CYMED_PRODUCT_PROFILE app filtering (standalone-products Phase 2 — see
[[cymed-standalone-products]]). Exercises core.settings._filter_product_apps
directly rather than booting 6 separate Django processes — the actual
boot-clean verification for all 6 profiles was done by hand via
`manage.py check` (see memory), this covers the filtering logic itself so
a future change to the app list can't silently break a profile.
"""
import pytest

from core import settings as cymed_settings

_SAMPLE_APPS = [
    "products.cymed.core.patients",
    "products.cymed.commercial.editions",
    "products.cymed.clinic.appointments",
    "products.cymed.hospital.adt",
    "products.cymed.hospital.nursing",
    "products.cymed.pharmacy.prescriptions",
    "products.cymed.pharmacy.dispensing",
    "products.cymed.laboratory.orders",
    "products.cymed.imaging.orders",
    "products.cymed.integrations.erx",
    "products.cymed.integrations.jofawtra",
    "products.cymed.simulations.apps.SimulationsConfig",
]


def _filter(profile):
    return cymed_settings._filter_product_apps(list(_SAMPLE_APPS), profile)


class TestFilterProductApps:
    def test_full_profile_is_unchanged(self):
        assert _filter("full") == _SAMPLE_APPS

    def test_unknown_profile_raises(self):
        with pytest.raises(ValueError, match="Unknown CYMED_PRODUCT_PROFILE"):
            _filter("radiology")

    def test_pharmacy_profile_keeps_only_pharmacy_and_shared(self):
        result = _filter("pharmacy")
        assert "products.cymed.pharmacy.prescriptions" in result
        assert "products.cymed.pharmacy.dispensing" in result
        assert "products.cymed.core.patients" in result
        assert "products.cymed.commercial.editions" in result
        assert "products.cymed.integrations.erx" in result  # pharmacy present
        assert "products.cymed.clinic.appointments" not in result
        assert "products.cymed.hospital.adt" not in result
        assert "products.cymed.laboratory.orders" not in result
        assert "products.cymed.imaging.orders" not in result
        assert "products.cymed.simulations.apps.SimulationsConfig" not in result

    def test_hospital_profile_carries_pharmacy_prescriptions_only(self):
        result = _filter("hospital")
        assert "products.cymed.hospital.adt" in result
        assert "products.cymed.hospital.nursing" in result
        assert "products.cymed.pharmacy.prescriptions" in result  # eMAR FK
        assert "products.cymed.pharmacy.dispensing" not in result  # not needed
        assert "products.cymed.integrations.erx" in result  # pharmacy present
        assert "products.cymed.clinic.appointments" not in result
        assert "products.cymed.simulations.apps.SimulationsConfig" not in result

    def test_clinic_profile_excludes_pharmacy_entirely(self):
        result = _filter("clinic")
        assert "products.cymed.clinic.appointments" in result
        assert "products.cymed.pharmacy.prescriptions" not in result
        assert "products.cymed.integrations.erx" not in result  # no pharmacy
        assert "products.cymed.hospital.adt" not in result

    def test_laboratory_and_imaging_profiles_exclude_everyone_else(self):
        lab = _filter("laboratory")
        assert "products.cymed.laboratory.orders" in lab
        assert "products.cymed.imaging.orders" not in lab
        assert "products.cymed.pharmacy.prescriptions" not in lab
        assert "products.cymed.integrations.erx" not in lab

        imaging = _filter("imaging")
        assert "products.cymed.imaging.orders" in imaging
        assert "products.cymed.laboratory.orders" not in imaging
