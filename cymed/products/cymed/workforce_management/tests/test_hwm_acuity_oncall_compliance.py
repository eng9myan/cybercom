"""
Tests for CyMed Workforce Management — Acuity, On-Call, Compliance, Float Pool modules.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

from django.test import TestCase

TENANT = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
FACILITY = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000001")
DEPT = uuid.UUID("cccccccc-0000-0000-0000-000000000001")
WARD = uuid.UUID("eeeeeeee-0000-0000-0000-000000000001")
PATIENT = uuid.UUID("ffffffff-0000-0000-0000-000000000001")
EMP_1 = uuid.UUID("dddddddd-0000-0000-0000-000000000001")
EMP_2 = uuid.UUID("dddddddd-0000-0000-0000-000000000002")


def _mk(**kwargs):
    return {"tenant_id": TENANT, **kwargs}


# ---------------------------------------------------------------------------
# Acuity Tests
# ---------------------------------------------------------------------------


class PatientAcuityScoreTest(TestCase):
    def test_acuity_level_1_stable(self):
        from products.cymed.workforce_management.acuity.models import PatientAcuityScore

        score = PatientAcuityScore.objects.create(
            **_mk(
                patient_id=PATIENT,
                ward_id=WARD,
                facility_id=FACILITY,
                acuity_level=1,
                news2_score=2,
                hppd_target=4.0,
                scored_at=datetime(2026, 7, 1, 8, 0, tzinfo=UTC),
            )
        )
        self.assertEqual(score.acuity_level, 1)
        self.assertEqual(score.hppd_target, 4.0)

    def test_acuity_level_4_intensive(self):
        from products.cymed.workforce_management.acuity.models import PatientAcuityScore

        score = PatientAcuityScore.objects.create(
            **_mk(
                patient_id=PATIENT,
                ward_id=WARD,
                facility_id=FACILITY,
                acuity_level=4,
                news2_score=12,
                hppd_target=21.0,
                scored_at=datetime(2026, 7, 1, 8, 0, tzinfo=UTC),
            )
        )
        self.assertEqual(score.acuity_level, 4)
        self.assertEqual(score.hppd_target, 21.0)


class WardCoverageRequirementTest(TestCase):
    def test_icu_coverage_requirement(self):
        from products.cymed.workforce_management.acuity.models import WardCoverageRequirement

        req = WardCoverageRequirement.objects.create(
            **_mk(
                facility_id=FACILITY,
                ward_type="icu",
                day_ratio_nurse=1,
                day_ratio_patients=2,
                night_ratio_nurse=1,
                night_ratio_patients=2,
                min_physician_on_site=1,
                physician_coverage_24_7=True,
                min_senior_nurse_pct=100,
                specialty_cert_required_100pct=True,
            )
        )
        self.assertEqual(req.ward_type, "icu")
        self.assertTrue(req.physician_coverage_24_7)
        self.assertTrue(req.specialty_cert_required_100pct)

    def test_med_surg_coverage_requirement(self):
        from products.cymed.workforce_management.acuity.models import WardCoverageRequirement

        req = WardCoverageRequirement.objects.create(
            **_mk(
                facility_id=FACILITY,
                ward_type="med_surg",
                day_ratio_nurse=1,
                day_ratio_patients=4,
                night_ratio_nurse=1,
                night_ratio_patients=6,
                min_physician_on_site=1,
            )
        )
        self.assertEqual(req.day_ratio_patients, 4)
        self.assertEqual(req.night_ratio_patients, 6)
        self.assertEqual(req.min_senior_nurse_pct, 30)

    def test_coverage_requirement_unique_per_ward_type(self):
        from django.db import IntegrityError

        from products.cymed.workforce_management.acuity.models import WardCoverageRequirement

        WardCoverageRequirement.objects.create(
            **_mk(
                facility_id=FACILITY,
                ward_type="nicu",
                day_ratio_nurse=1,
                day_ratio_patients=1,
            )
        )
        with self.assertRaises(IntegrityError):
            WardCoverageRequirement.objects.create(
                **_mk(
                    facility_id=FACILITY,
                    ward_type="nicu",
                    day_ratio_nurse=1,
                    day_ratio_patients=2,
                )
            )


class SkillMixValidationTest(TestCase):
    def test_skill_mix_pass(self):
        from products.cymed.workforce_management.acuity.models import SkillMixValidation

        v = SkillMixValidation.objects.create(
            **_mk(
                roster_cycle_id=uuid.uuid4(),
                ward_id=WARD,
                slot_date=date(2026, 7, 5),
                shift_type="12h_day",
                charge_nurse_present=True,
                total_nurses_scheduled=5,
                senior_nurse_count=2,
                senior_nurse_pct=40.00,
                specialty_cert_pct=100.00,
                passed=True,
            )
        )
        self.assertTrue(v.passed)
        self.assertTrue(v.charge_nurse_present)

    def test_skill_mix_fail_no_charge_nurse(self):
        from products.cymed.workforce_management.acuity.models import SkillMixValidation

        v = SkillMixValidation.objects.create(
            **_mk(
                roster_cycle_id=uuid.uuid4(),
                ward_id=WARD,
                slot_date=date(2026, 7, 5),
                shift_type="12h_night",
                charge_nurse_present=False,
                total_nurses_scheduled=4,
                senior_nurse_count=1,
                senior_nurse_pct=25.00,
                specialty_cert_pct=100.00,
                passed=False,
                failure_reasons=["charge_nurse_missing", "senior_nurse_pct_below_30"],
            )
        )
        self.assertFalse(v.passed)
        self.assertIn("charge_nurse_missing", v.failure_reasons)


# ---------------------------------------------------------------------------
# On-Call Tests
# ---------------------------------------------------------------------------


class OnCallRosterTest(TestCase):
    def _roster(self, status="draft"):
        from products.cymed.workforce_management.oncall.models import OnCallRoster

        return OnCallRoster.objects.create(
            **_mk(
                facility_id=FACILITY,
                department_id=DEPT,
                specialty="Cardiology",
                roster_date=date(2026, 7, 5),
                status=status,
            )
        )

    def test_roster_creation(self):
        roster = self._roster()
        self.assertEqual(roster.specialty, "Cardiology")
        self.assertEqual(roster.status, "draft")

    def test_oncall_assignment(self):
        from products.cymed.workforce_management.oncall.models import OnCallAssignment

        roster = self._roster()
        assignment = OnCallAssignment.objects.create(
            **_mk(
                oncall_roster=roster,
                workforce_profile_id=EMP_1,
                call_mode="in_house",
                call_tier="primary",
                call_seniority="consultant",
                response_sla_minutes=5,
            )
        )
        self.assertEqual(assignment.call_tier, "primary")
        self.assertEqual(assignment.call_mode, "in_house")
        self.assertEqual(assignment.response_sla_minutes, 5)

    def test_roster_requires_primary_and_secondary(self):
        from products.cymed.workforce_management.oncall.models import OnCallAssignment

        roster = self._roster()
        OnCallAssignment.objects.create(
            **_mk(
                oncall_roster=roster,
                workforce_profile_id=EMP_1,
                call_mode="in_house",
                call_tier="primary",
                call_seniority="consultant",
            )
        )
        OnCallAssignment.objects.create(
            **_mk(
                oncall_roster=roster,
                workforce_profile_id=EMP_2,
                call_mode="home_call",
                call_tier="secondary",
                call_seniority="consultant",
            )
        )
        self.assertEqual(roster.assignments.count(), 2)


class OnCallPageTest(TestCase):
    def _page(self, urgency="urgent"):
        from products.cymed.workforce_management.oncall.models import OnCallPage, OnCallRoster

        roster = OnCallRoster.objects.create(
            **_mk(
                facility_id=FACILITY,
                department_id=DEPT,
                specialty="General Surgery",
                roster_date=date(2026, 7, 5),
            )
        )
        now = datetime.now(tz=UTC)
        return OnCallPage.objects.create(
            **_mk(
                oncall_roster=roster,
                initiating_ward_id=WARD,
                patient_id=PATIENT,
                urgency=urgency,
                clinical_reason="Post-op bleeding",
                status="sent",
                sla_deadline=now + timedelta(minutes=10),
            )
        )

    def test_page_creation(self):
        page = self._page()
        self.assertEqual(page.status, "sent")
        self.assertEqual(page.urgency, "urgent")
        self.assertIsNotNone(page.sla_deadline)

    def test_page_escalation(self):
        from products.cymed.workforce_management.oncall.models import OnCallEscalation

        page = self._page(urgency="emergent")
        now = datetime.now(tz=UTC)
        escalation = OnCallEscalation.objects.create(
            **_mk(
                page=page,
                escalation_level=1,
                escalated_to_profile_id=EMP_2,
                sla_deadline=now + timedelta(minutes=10),
            )
        )
        self.assertEqual(escalation.escalation_level, 1)
        self.assertFalse(escalation.department_chair_alerted)

    def test_page_level2_escalation_alerts_chair(self):
        from products.cymed.workforce_management.oncall.models import OnCallEscalation

        page = self._page(urgency="critical")
        escalation = OnCallEscalation.objects.create(
            **_mk(
                page=page,
                escalation_level=2,
                escalated_to_profile_id=EMP_2,
                department_chair_alerted=True,
            )
        )
        self.assertTrue(escalation.department_chair_alerted)


# ---------------------------------------------------------------------------
# Compliance Tests
# ---------------------------------------------------------------------------


class WorkforceComplianceConfigTest(TestCase):
    def test_saudi_arabia_config(self):
        from products.cymed.workforce_management.compliance.models import WorkforceComplianceConfig

        config = WorkforceComplianceConfig.objects.create(
            **_mk(
                country_code="SAU",
                region_code="ALL",
                max_weekly_hours=48,
                max_consecutive_days=6,
                min_rest_hours_between_shifts=11,
                overtime_threshold_daily_hours=8,
                accreditation_body="CBAHI",
                mandatory_shift_supervisor=True,
                credential_verification_frequency_days=365,
            )
        )
        self.assertEqual(config.country_code, "SAU")
        self.assertEqual(config.max_weekly_hours, 48)
        self.assertEqual(config.accreditation_body, "CBAHI")

    def test_ramadan_rule(self):
        from products.cymed.workforce_management.compliance.models import (
            RamadanComplianceRule,
            WorkforceComplianceConfig,
        )

        config = WorkforceComplianceConfig.objects.create(
            **_mk(
                country_code="SAU",
                region_code="ALL",
                max_weekly_hours=48,
                min_rest_hours_between_shifts=11,
                max_consecutive_days=6,
                accreditation_body="CBAHI",
            )
        )
        rule = RamadanComplianceRule.objects.create(
            **_mk(
                compliance_config=config,
                muslim_max_daily_hours=6,
                muslim_max_weekly_hours=36,
            )
        )
        self.assertEqual(rule.muslim_max_daily_hours, 6)
        self.assertEqual(rule.muslim_max_weekly_hours, 36)
        self.assertEqual(rule.ramadan_hijri_month, 9)

    def test_usa_california_config(self):
        from products.cymed.workforce_management.compliance.models import (
            WardRatioConfig,
            WorkforceComplianceConfig,
        )

        config = WorkforceComplianceConfig.objects.create(
            **_mk(
                country_code="USA",
                region_code="CA",
                max_weekly_hours=40,
                max_consecutive_days=6,
                min_rest_hours_between_shifts=8,
                overtime_threshold_daily_hours=8,
                accreditation_body="TJC",
            )
        )
        WardRatioConfig.objects.create(
            **_mk(
                compliance_config=config,
                ward_type="icu",
                day_ratio_nurse=1,
                day_ratio_patients=2,
                night_ratio_nurse=1,
                night_ratio_patients=2,
            )
        )
        WardRatioConfig.objects.create(
            **_mk(
                compliance_config=config,
                ward_type="med_surg",
                day_ratio_nurse=1,
                day_ratio_patients=5,
                night_ratio_nurse=1,
                night_ratio_patients=5,
            )
        )
        self.assertEqual(config.ward_ratios.count(), 2)

    def test_compliance_config_unique_per_country_region(self):
        from django.db import IntegrityError

        from products.cymed.workforce_management.compliance.models import WorkforceComplianceConfig

        WorkforceComplianceConfig.objects.create(
            **_mk(
                country_code="JOR",
                region_code="ALL",
                max_weekly_hours=48,
                min_rest_hours_between_shifts=10,
                max_consecutive_days=6,
                accreditation_body="JCIA",
            )
        )
        with self.assertRaises(IntegrityError):
            WorkforceComplianceConfig.objects.create(
                **_mk(
                    country_code="JOR",
                    region_code="ALL",
                    max_weekly_hours=40,
                    min_rest_hours_between_shifts=10,
                    max_consecutive_days=5,
                    accreditation_body="JCIA",
                )
            )


# ---------------------------------------------------------------------------
# Float Pool Tests
# ---------------------------------------------------------------------------


class FloatPoolTest(TestCase):
    def test_float_member_creation(self):
        from products.cymed.workforce_management.float_pool.models import FloatPoolMember

        member = FloatPoolMember.objects.create(
            **_mk(
                workforce_profile_id=EMP_1,
                facility_id=FACILITY,
                eligible_ward_types=["med_surg", "icu", "ed"],
                priority_score=80,
                is_network_float=False,
            )
        )
        self.assertEqual(member.priority_score, 80)
        self.assertIn("icu", member.eligible_ward_types)

    def test_float_deployment(self):
        from products.cymed.workforce_management.float_pool.models import (
            FloatDeployment,
            FloatPoolMember,
        )

        member = FloatPoolMember.objects.create(
            **_mk(
                workforce_profile_id=EMP_1,
                facility_id=FACILITY,
            )
        )
        deployment = FloatDeployment.objects.create(
            **_mk(
                float_member=member,
                target_department_id=DEPT,
                target_facility_id=FACILITY,
                status="deployed",
                deployment_reason="Shortage in pediatric ICU day shift",
            )
        )
        self.assertEqual(deployment.status, "deployed")

    def test_agency_staff_verification_flow(self):
        from products.cymed.workforce_management.float_pool.models import AgencyStaffRegistration

        staff = AgencyStaffRegistration.objects.create(
            **_mk(
                facility_id=FACILITY,
                agency_name="NurseTravel Corp",
                display_name="Maria Gonzalez",
                specialty="Critical Care",
                role_type="icu_nurse",
                contract_start=date(2026, 7, 1),
                contract_end=date(2026, 9, 30),
                status="pending_verification",
            )
        )
        self.assertFalse(staff.credential_verified)
        self.assertFalse(staff.identity_verified)
        self.assertFalse(staff.ehr_access_token_issued)

        staff.credential_verified = True
        staff.save()
        self.assertFalse(staff.ehr_access_token_issued)

        staff.identity_verified = True
        staff.ehr_access_token_issued = True
        staff.status = "active"
        staff.save()
        staff.refresh_from_db()
        self.assertTrue(staff.ehr_access_token_issued)
        self.assertEqual(staff.status, "active")

    def test_shortage_alert_diversion(self):
        from products.cymed.workforce_management.float_pool.models import StaffingShortageAlert

        alert = StaffingShortageAlert.objects.create(
            **_mk(
                facility_id=FACILITY,
                department_id=DEPT,
                roster_slot_id=uuid.uuid4(),
                escalation_level="level_3",
                diversion_activated=True,
            )
        )
        self.assertEqual(alert.escalation_level, "level_3")
        self.assertTrue(alert.diversion_activated)
