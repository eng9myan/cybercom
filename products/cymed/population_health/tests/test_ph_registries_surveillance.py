"""
Tests for CyMed Population Health — Registries, Public Health, Surveillance modules.
"""

import uuid

from django.test import TestCase

TENANT = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
PATIENT = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000001")
PROVIDER = uuid.UUID("cccccccc-0000-0000-0000-000000000001")
FACILITY = uuid.UUID("dddddddd-0000-0000-0000-000000000001")


def _mk(**kwargs):
    """Build model kwargs with default tenant."""
    return {"tenant_id": TENANT, **kwargs}


# ---------------------------------------------------------------------------
# Registries Tests
# ---------------------------------------------------------------------------


class DiseaseRegistryTest(TestCase):
    def _registry(self, name="Diabetes Registry", registry_type="diabetes"):
        from products.cymed.population_health.registries.models import DiseaseRegistry

        return DiseaseRegistry.objects.create(
            **_mk(
                name=name,
                registry_type=registry_type,
                start_date="2024-01-01",
                is_national=True,
                managing_authority="Ministry of Health",
            )
        )

    def test_registry_creation(self):
        reg = self._registry()
        self.assertEqual(reg.name, "Diabetes Registry")
        self.assertEqual(reg.registry_type, "diabetes")
        self.assertTrue(reg.is_national)
        self.assertTrue(reg.is_active)

    def test_registry_code_optional(self):
        reg = self._registry()
        reg.registry_code = "DM-NAT-001"
        reg.save()
        self.assertEqual(reg.registry_code, "DM-NAT-001")

    def test_registry_icd11_codes_json(self):
        from products.cymed.population_health.registries.models import DiseaseRegistry

        reg = DiseaseRegistry.objects.create(
            **_mk(
                name="Cancer Registry",
                registry_type="cancer",
                start_date="2022-01-01",
                icd11_codes=["2C10", "2C20", "XH9184"],
            )
        )
        self.assertEqual(len(reg.icd11_codes), 3)
        self.assertIn("2C10", reg.icd11_codes)

    def test_registry_patient_enrollment(self):
        from products.cymed.population_health.registries.models import (
            RegistryPatient,
        )

        reg = self._registry()
        rp = RegistryPatient.objects.create(
            **_mk(
                registry=reg,
                patient_id=PATIENT,
                enrollment_date="2024-02-01",
                status="active",
                enrollment_source="clinical",
            )
        )
        self.assertEqual(rp.status, "active")
        self.assertEqual(rp.enrollment_source, "clinical")

    def test_registry_patient_unique_per_registry(self):
        from django.db import IntegrityError

        from products.cymed.population_health.registries.models import (
            RegistryPatient,
        )

        reg = self._registry()
        RegistryPatient.objects.create(
            **_mk(
                registry=reg,
                patient_id=PATIENT,
                enrollment_date="2024-01-01",
            )
        )
        with self.assertRaises(IntegrityError):
            RegistryPatient.objects.create(
                **_mk(
                    registry=reg,
                    patient_id=PATIENT,
                    enrollment_date="2024-06-01",
                )
            )

    def test_registry_status_history(self):
        from products.cymed.population_health.registries.models import (
            RegistryPatient,
            RegistryStatus,
        )

        reg = self._registry()
        rp = RegistryPatient.objects.create(
            **_mk(
                registry=reg,
                patient_id=PATIENT,
                enrollment_date="2024-01-01",
            )
        )
        rs = RegistryStatus.objects.create(
            **_mk(
                registry_patient=rp,
                status_date="2024-06-01",
                status="inactive",
                changed_by_user_id=PROVIDER,
                reason="Patient relocated",
            )
        )
        self.assertEqual(rs.status, "inactive")

    def test_registry_outcome_recorded(self):
        from products.cymed.population_health.registries.models import (
            RegistryOutcome,
            RegistryPatient,
        )

        reg = self._registry()
        rp = RegistryPatient.objects.create(
            **_mk(
                registry=reg,
                patient_id=PATIENT,
                enrollment_date="2024-01-01",
            )
        )
        out = RegistryOutcome.objects.create(
            **_mk(
                registry_patient=rp,
                outcome_type="remission",
                outcome_date="2025-03-01",
                icd11_code="5A10",
                reporting_provider_id=PROVIDER,
            )
        )
        self.assertEqual(out.outcome_type, "remission")


# ---------------------------------------------------------------------------
# Public Health Tests
# ---------------------------------------------------------------------------


class PopulationGroupTest(TestCase):
    def test_population_group_creation(self):
        from products.cymed.population_health.public_health.models import PopulationGroup

        grp = PopulationGroup.objects.create(
            **_mk(
                name="Diabetic Adults 40+",
                group_type="clinical",
                criteria={"age_min": 40, "conditions": ["diabetes"]},
                estimated_size=12000,
            )
        )
        self.assertEqual(grp.group_type, "clinical")
        self.assertEqual(grp.criteria["age_min"], 40)

    def test_population_segment(self):
        from products.cymed.population_health.public_health.models import (
            PopulationGroup,
            PopulationSegment,
        )

        grp = PopulationGroup.objects.create(
            **_mk(
                name="High Risk Hypertension",
                group_type="risk",
                estimated_size=5000,
            )
        )
        seg = PopulationSegment.objects.create(
            **_mk(
                population_group=grp,
                segment_name="Uncontrolled HTN",
                segment_criteria={"bp_systolic_gt": 160},
                patient_count=800,
            )
        )
        self.assertEqual(seg.patient_count, 800)

    def test_health_risk_ai_advisory_only(self):

        from products.cymed.population_health.public_health.models import HealthRisk

        risk = HealthRisk.objects.create(
            **_mk(
                patient_id=PATIENT,
                risk_type="cardiovascular",
                risk_level="high",
                risk_score="72.50",
                assessment_date="2025-01-01",
                is_ai_generated=True,
            )
        )
        self.assertTrue(risk.is_ai_generated)
        self.assertEqual(risk.risk_level, "high")

    def test_health_goal_lifecycle(self):
        from products.cymed.population_health.public_health.models import HealthGoal

        goal = HealthGoal.objects.create(
            **_mk(
                patient_id=PATIENT,
                goal_type="weight_loss",
                target_value="85",
                current_value="92",
                unit="kg",
                start_date="2025-01-01",
                status="active",
            )
        )
        goal.current_value = "87"
        goal.save()
        self.assertEqual(goal.current_value, "87")

    def test_national_provider_registration(self):
        from products.cymed.population_health.public_health.models import NationalProvider

        np = NationalProvider.objects.create(
            **_mk(
                provider_id=PROVIDER,
                national_provider_number="SAU-MD-12345",
                provider_type="physician",
                specialty="Internal Medicine",
                registration_date="2020-01-01",
                registration_status="active",
            )
        )
        self.assertEqual(np.national_provider_number, "SAU-MD-12345")
        self.assertEqual(np.registration_status, "active")

    def test_national_facility_registration(self):
        from products.cymed.population_health.public_health.models import NationalFacility

        fac = NationalFacility.objects.create(
            **_mk(
                facility_id=FACILITY,
                national_facility_number="SAU-HOSP-001",
                facility_type="hospital",
                facility_name="King Faisal Medical City",
                license_status="active",
                registration_date="2015-01-01",
                beds_count=400,
            )
        )
        self.assertEqual(fac.license_status, "active")
        self.assertEqual(fac.beds_count, 400)


# ---------------------------------------------------------------------------
# Surveillance Tests
# ---------------------------------------------------------------------------


class SurveillanceTest(TestCase):
    def test_surveillance_case_creation(self):
        from products.cymed.population_health.surveillance.models import SurveillanceCase

        case = SurveillanceCase.objects.create(
            **_mk(
                patient_id=PATIENT,
                disease_code="1C62",
                disease_name="COVID-19",
                case_type="confirmed",
                case_date="2025-01-15",
                reporting_facility_id=FACILITY,
                is_notifiable=True,
                status="open",
            )
        )
        self.assertEqual(case.case_type, "confirmed")
        self.assertTrue(case.is_notifiable)
        self.assertFalse(case.notification_sent)

    def test_outbreak_creation(self):
        from products.cymed.population_health.surveillance.models import Outbreak

        outbreak = Outbreak.objects.create(
            **_mk(
                disease_code="1C62",
                disease_name="COVID-19",
                outbreak_type="cluster",
                start_date="2025-01-10",
                geographic_scope="Riyadh Region",
                affected_count=35,
                confirmed_count=28,
                status="active",
                severity_level="high",
            )
        )
        self.assertEqual(outbreak.severity_level, "high")
        self.assertEqual(outbreak.status, "active")

    def test_outbreak_alert_escalation(self):
        from products.cymed.population_health.surveillance.models import Outbreak, OutbreakAlert

        outbreak = Outbreak.objects.create(
            **_mk(
                disease_code="1D47",
                disease_name="Measles",
                outbreak_type="epidemic",
                start_date="2025-02-01",
                status="active",
                severity_level="critical",
            )
        )
        alert = OutbreakAlert.objects.create(
            **_mk(
                outbreak=outbreak,
                alert_level="red",
                description="Measles outbreak exceeds threshold — mandatory IHR notification",
                recommended_actions=["activate_response_team", "notify_who"],
            )
        )
        self.assertEqual(alert.alert_level, "red")
        self.assertTrue(alert.is_active)

    def test_public_health_event(self):
        from products.cymed.population_health.surveillance.models import PublicHealthEvent

        event = PublicHealthEvent.objects.create(
            **_mk(
                event_type="vaccination_drive",
                event_name="National Flu Vaccination Campaign 2025",
                event_date="2025-10-01",
                end_date="2025-10-31",
                severity="low",
                response_status="planning",
            )
        )
        self.assertEqual(event.event_type, "vaccination_drive")

    def test_case_investigation(self):
        from products.cymed.population_health.surveillance.models import (
            CaseInvestigation,
            SurveillanceCase,
        )

        case = SurveillanceCase.objects.create(
            **_mk(
                patient_id=PATIENT,
                disease_code="1A90",
                disease_name="Typhoid",
                case_type="probable",
                case_date="2025-03-01",
                is_notifiable=True,
                status="under_investigation",
            )
        )
        inv = CaseInvestigation.objects.create(
            **_mk(
                surveillance_case=case,
                investigator_id=PROVIDER,
                investigation_date="2025-03-02",
                exposure_history="Consumed food from street vendor 7 days prior",
                contacts_identified=12,
                contacts_traced=10,
                contacts_tested=8,
                outcome="ongoing",
            )
        )
        self.assertEqual(inv.contacts_traced, 10)
        self.assertEqual(inv.outcome, "ongoing")


# ---------------------------------------------------------------------------
# Tenant Isolation Test
# ---------------------------------------------------------------------------


class TenantIsolationTest(TestCase):
    def test_registry_tenant_isolation(self):
        from products.cymed.population_health.registries.models import DiseaseRegistry

        tenant_a = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
        tenant_b = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000002")
        DiseaseRegistry.objects.create(
            tenant_id=tenant_a, name="Reg A", registry_type="diabetes", start_date="2024-01-01"
        )
        DiseaseRegistry.objects.create(
            tenant_id=tenant_b, name="Reg B", registry_type="cancer", start_date="2024-01-01"
        )
        self.assertEqual(DiseaseRegistry.objects.filter(tenant_id=tenant_a).count(), 1)
        self.assertEqual(DiseaseRegistry.objects.filter(tenant_id=tenant_b).count(), 1)

    def test_surveillance_case_tenant_isolation(self):
        from products.cymed.population_health.surveillance.models import SurveillanceCase

        tenant_a = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
        tenant_b = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000002")
        SurveillanceCase.objects.create(
            tenant_id=tenant_a,
            patient_id=PATIENT,
            disease_code="1C62",
            disease_name="COVID-19",
            case_type="confirmed",
            case_date="2025-01-01",
        )
        SurveillanceCase.objects.create(
            tenant_id=tenant_b,
            patient_id=PATIENT,
            disease_code="1C62",
            disease_name="COVID-19",
            case_type="suspected",
            case_date="2025-01-01",
        )
        self.assertEqual(SurveillanceCase.objects.filter(tenant_id=tenant_a).count(), 1)
        self.assertEqual(SurveillanceCase.objects.filter(tenant_id=tenant_b).count(), 1)
