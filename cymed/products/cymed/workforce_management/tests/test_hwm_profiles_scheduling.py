"""
Tests for CyMed Workforce Management — Profiles, Scheduling, Shift Swaps modules.
"""

import uuid
from datetime import UTC, date, datetime, time

from django.test import TestCase

TENANT = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
FACILITY = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000001")
DEPT = uuid.UUID("cccccccc-0000-0000-0000-000000000001")
EMP_1 = uuid.UUID("dddddddd-0000-0000-0000-000000000001")
EMP_2 = uuid.UUID("dddddddd-0000-0000-0000-000000000002")


def _mk(**kwargs):
    return {"tenant_id": TENANT, **kwargs}


# ---------------------------------------------------------------------------
# Workforce Profiles Tests
# ---------------------------------------------------------------------------


class WorkforceProfileTest(TestCase):
    def _profile(self, emp=EMP_1, role="staff_nurse"):
        from products.cymed.workforce_management.workforce_profiles.models import WorkforceProfile

        return WorkforceProfile.objects.create(
            **_mk(
                employee_id=emp,
                facility_id=FACILITY,
                display_name="Jane Smith",
                role_type=role,
                clinical_category="nursing",
                contract_type="full_time",
                specialty="Medical-Surgical",
            )
        )

    def test_profile_creation(self):
        profile = self._profile()
        self.assertEqual(profile.role_type, "staff_nurse")
        self.assertEqual(profile.clinical_category, "nursing")
        self.assertTrue(profile.is_active)
        self.assertTrue(profile.can_self_schedule)

    def test_profile_float_eligible_default_false(self):
        profile = self._profile()
        self.assertFalse(profile.is_float_eligible)

    def test_profile_deactivation(self):
        profile = self._profile()
        profile.is_active = False
        profile.save()
        profile.refresh_from_db()
        self.assertFalse(profile.is_active)

    def test_physician_profile(self):
        from products.cymed.workforce_management.workforce_profiles.models import WorkforceProfile

        profile = WorkforceProfile.objects.create(
            **_mk(
                employee_id=EMP_2,
                facility_id=FACILITY,
                display_name="Dr. Ahmed Al-Rashid",
                role_type="resident",
                clinical_category="physician",
                contract_type="resident_training",
                specialty="Internal Medicine",
            )
        )
        self.assertEqual(profile.role_type, "resident")
        self.assertEqual(profile.contract_type, "resident_training")


class ClinicalCredentialTest(TestCase):
    def _profile(self):
        from products.cymed.workforce_management.workforce_profiles.models import WorkforceProfile

        return WorkforceProfile.objects.create(
            **_mk(
                employee_id=EMP_1,
                facility_id=FACILITY,
                display_name="Sarah Jones",
                role_type="icu_nurse",
                clinical_category="nursing",
            )
        )

    def test_credential_creation(self):
        from products.cymed.workforce_management.workforce_profiles.models import ClinicalCredential

        profile = self._profile()
        cred = ClinicalCredential.objects.create(
            **_mk(
                profile=profile,
                credential_type="acls",
                issuing_body="American Heart Association",
                credential_number="ACLS-2024-001",
                issued_date=date(2024, 1, 15),
                expiry_date=date(2026, 1, 15),
                status="valid",
            )
        )
        self.assertEqual(cred.credential_type, "acls")
        self.assertEqual(cred.status, "valid")

    def test_credential_expiry_status(self):
        from products.cymed.workforce_management.workforce_profiles.models import ClinicalCredential

        profile = self._profile()
        cred = ClinicalCredential.objects.create(
            **_mk(
                profile=profile,
                credential_type="bls",
                expiry_date=date(2025, 12, 31),
                status="expiring_soon",
            )
        )
        self.assertEqual(cred.status, "expiring_soon")


class CompetencyRecordTest(TestCase):
    def _profile(self):
        from products.cymed.workforce_management.workforce_profiles.models import WorkforceProfile

        return WorkforceProfile.objects.create(
            **_mk(
                employee_id=EMP_1,
                facility_id=FACILITY,
                display_name="Robert Kim",
                role_type="icu_nurse",
                clinical_category="nursing",
            )
        )

    def test_competency_creation(self):
        from products.cymed.workforce_management.workforce_profiles.models import CompetencyRecord

        profile = self._profile()
        comp = CompetencyRecord.objects.create(
            **_mk(
                profile=profile,
                competency_code="ICU_VENT_MGMT",
                competency_name="Ventilator Management",
                certified_at=date(2024, 3, 1),
                expiry_date=date(2026, 3, 1),
            )
        )
        self.assertTrue(comp.is_current)
        self.assertEqual(comp.competency_code, "ICU_VENT_MGMT")

    def test_competency_unique_per_profile(self):
        from django.db import IntegrityError

        from products.cymed.workforce_management.workforce_profiles.models import CompetencyRecord

        profile = self._profile()
        CompetencyRecord.objects.create(
            **_mk(
                profile=profile,
                competency_code="BLS",
                competency_name="Basic Life Support",
                certified_at=date(2024, 1, 1),
            )
        )
        with self.assertRaises(IntegrityError):
            CompetencyRecord.objects.create(
                **_mk(
                    profile=profile,
                    competency_code="BLS",
                    competency_name="Basic Life Support",
                    certified_at=date(2024, 6, 1),
                )
            )


# ---------------------------------------------------------------------------
# Scheduling Tests
# ---------------------------------------------------------------------------


class ShiftTemplateTest(TestCase):
    def _template(self, name="12h Day ICU", shift_type="12h_day"):
        from products.cymed.workforce_management.scheduling.models import ShiftTemplate

        return ShiftTemplate.objects.create(
            **_mk(
                name=name,
                shift_type=shift_type,
                start_time=time(7, 0),
                end_time=time(19, 0),
                duration_hours=12,
                break_minutes=30,
                handover_minutes=30,
            )
        )

    def test_shift_template_creation(self):
        tmpl = self._template()
        self.assertEqual(tmpl.shift_type, "12h_day")
        self.assertEqual(tmpl.duration_hours, 12)
        self.assertTrue(tmpl.is_active)

    def test_8h_shift_template(self):
        from products.cymed.workforce_management.scheduling.models import ShiftTemplate

        tmpl = ShiftTemplate.objects.create(
            **_mk(
                name="8h Morning",
                shift_type="8h_morning",
                start_time=time(7, 0),
                end_time=time(15, 0),
                duration_hours=8,
                break_minutes=0,
            )
        )
        self.assertEqual(tmpl.duration_hours, 8)


class RosterCycleTest(TestCase):
    def _cycle(self, status="draft"):
        from products.cymed.workforce_management.scheduling.models import RosterCycle

        return RosterCycle.objects.create(
            **_mk(
                facility_id=FACILITY,
                department_id=DEPT,
                period_start=date(2026, 7, 1),
                period_end=date(2026, 7, 31),
                status=status,
            )
        )

    def test_cycle_creation(self):
        cycle = self._cycle()
        self.assertEqual(cycle.status, "draft")
        self.assertEqual(cycle.period_start, date(2026, 7, 1))

    def test_cycle_publish(self):
        cycle = self._cycle()
        cycle.status = "published"
        cycle.save()
        cycle.refresh_from_db()
        self.assertEqual(cycle.status, "published")


class RosterSlotTest(TestCase):
    def _slot(self):
        from products.cymed.workforce_management.scheduling.models import (
            RosterCycle,
            RosterSlot,
            ShiftTemplate,
        )

        tmpl = ShiftTemplate.objects.create(
            **_mk(
                name="12h Day",
                shift_type="12h_day",
                start_time=time(7, 0),
                end_time=time(19, 0),
                duration_hours=12,
            )
        )
        cycle = RosterCycle.objects.create(
            **_mk(
                facility_id=FACILITY,
                department_id=DEPT,
                period_start=date(2026, 7, 1),
                period_end=date(2026, 7, 31),
            )
        )
        return RosterSlot.objects.create(
            **_mk(
                roster_cycle=cycle,
                workforce_profile_id=EMP_1,
                shift_template=tmpl,
                slot_date=date(2026, 7, 5),
                status="scheduled",
            )
        )

    def test_slot_creation(self):
        slot = self._slot()
        self.assertEqual(slot.status, "scheduled")
        self.assertEqual(slot.slot_date, date(2026, 7, 5))

    def test_slot_check_in(self):
        slot = self._slot()
        slot.status = "checked_in"
        slot.checked_in_at = datetime(2026, 7, 5, 7, 0, tzinfo=UTC)
        slot.save()
        slot.refresh_from_db()
        self.assertEqual(slot.status, "checked_in")
        self.assertIsNotNone(slot.checked_in_at)

    def test_slot_completion(self):
        slot = self._slot()
        slot.status = "completed"
        slot.checked_out_at = datetime(2026, 7, 5, 19, 0, tzinfo=UTC)
        slot.save()
        slot.refresh_from_db()
        self.assertEqual(slot.status, "completed")


# ---------------------------------------------------------------------------
# Shift Swaps Tests
# ---------------------------------------------------------------------------


class ShiftSwapRequestTest(TestCase):
    def _swap(self, requester_slot=None, recipient_slot=None):
        from products.cymed.workforce_management.shift_swaps.models import ShiftSwapRequest

        return ShiftSwapRequest.objects.create(
            **_mk(
                requester_profile_id=EMP_1,
                recipient_profile_id=EMP_2,
                requester_slot_id=requester_slot or uuid.uuid4(),
                recipient_slot_id=recipient_slot or uuid.uuid4(),
                status="pending_recipient",
            )
        )

    def test_swap_creation(self):
        swap = self._swap()
        self.assertEqual(swap.status, "pending_recipient")
        self.assertEqual(swap.requester_profile_id, EMP_1)
        self.assertEqual(swap.recipient_profile_id, EMP_2)

    def test_swap_accept(self):
        swap = self._swap()
        swap.status = "pending_validation"
        swap.save()
        swap.refresh_from_db()
        self.assertEqual(swap.status, "pending_validation")

    def test_swap_commit(self):
        swap = self._swap()
        swap.status = "committed"
        swap.save()
        swap.refresh_from_db()
        self.assertEqual(swap.status, "committed")

    def test_swap_rejection_reason(self):
        from products.cymed.workforce_management.shift_swaps.models import ShiftSwapRequest

        swap = ShiftSwapRequest.objects.create(
            **_mk(
                requester_profile_id=EMP_1,
                requester_slot_id=uuid.uuid4(),
                status="rejected",
                rejection_reason="fatigue_violation",
                rejection_detail="Clinician has worked 72 hours this week — cannot assign additional shift.",
            )
        )
        self.assertEqual(swap.rejection_reason, "fatigue_violation")


class SwapValidationLogTest(TestCase):
    def test_validation_log(self):
        from products.cymed.workforce_management.shift_swaps.models import (
            ShiftSwapRequest,
            SwapValidationLog,
        )

        swap = ShiftSwapRequest.objects.create(
            **_mk(
                requester_profile_id=EMP_1,
                requester_slot_id=uuid.uuid4(),
                status="pending_validation",
            )
        )
        log = SwapValidationLog.objects.create(
            **_mk(
                swap_request=swap,
                check_type="rest_period_check",
                passed=True,
                detail="11h rest period satisfied",
            )
        )
        self.assertTrue(log.passed)
        self.assertEqual(log.check_type, "rest_period_check")

    def test_validation_failure_log(self):
        from products.cymed.workforce_management.shift_swaps.models import (
            ShiftSwapRequest,
            SwapValidationLog,
        )

        swap = ShiftSwapRequest.objects.create(
            **_mk(
                requester_profile_id=EMP_1,
                requester_slot_id=uuid.uuid4(),
                status="rejected",
            )
        )
        log = SwapValidationLog.objects.create(
            **_mk(
                swap_request=swap,
                check_type="credential_check",
                passed=False,
                detail="Recipient lacks ICU specialty certification required for this ward.",
            )
        )
        self.assertFalse(log.passed)
