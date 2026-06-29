"""
Tests for CyMed RCM — Insurance, Eligibility, Preauthorization, Charge Capture.
"""

import uuid
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from products.cymed.rcm.charge_capture.models import (
    Charge,
    ChargeAudit,
    ChargeItem,
    ChargeRule,
)
from products.cymed.rcm.eligibility.models import (
    BenefitVerification,
    CoverageVerification,
    EligibilityRequest,
    EligibilityResponse,
)
from products.cymed.rcm.insurance.models import (
    Benefit,
    Coverage,
    CoverageRule,
    InsuranceCard,
    InsuranceCompany,
    InsuranceMember,
    InsurancePlan,
)
from products.cymed.rcm.preauthorization.models import (
    AuthorizationAppeal,
    AuthorizationDecision,
    AuthorizationRequest,
    Preauthorization,
)

TENANT = uuid.uuid4()


def make_company(**kwargs):
    defaults = {
        "tenant_id": TENANT,
        "name": "Gulf Insurance Co",
        "short_name": "GIC",
        "company_type": "private",
        "payer_id": str(uuid.uuid4())[:10],
        "country": "SAU",
        "is_active": True,
    }
    defaults.update(kwargs)
    return InsuranceCompany.objects.create(**defaults)


def make_plan(company, **kwargs):
    defaults = {
        "tenant_id": TENANT,
        "company": company,
        "plan_name": "Gold Plan",
        "plan_code": "GOLD-001",
        "plan_type": "ppo",
        "network_type": "both",
        "coverage_category": "premium",
        "is_active": True,
    }
    defaults.update(kwargs)
    return InsurancePlan.objects.create(**defaults)


def make_member(plan, patient_id=None, **kwargs):
    defaults = {
        "tenant_id": TENANT,
        "patient_id": patient_id or uuid.uuid4(),
        "insurance_plan": plan,
        "member_id": "MEM-001",
        "member_relationship": "self",
        "is_primary_holder": True,
        "effective_date": timezone.now().date(),
        "is_active": True,
        "priority_order": 1,
    }
    defaults.update(kwargs)
    return InsuranceMember.objects.create(**defaults)


# ─── Insurance ────────────────────────────────────────────────────────────────


class InsuranceCompanyTest(TestCase):
    def test_create_company(self):
        co = make_company()
        self.assertEqual(co.name, "Gulf Insurance Co")
        self.assertEqual(co.company_type, "private")
        self.assertEqual(co.country, "SAU")
        self.assertTrue(co.is_active)

    def test_company_payer_id_unique(self):
        make_company(payer_id="UNIQUE-001")
        with self.assertRaises(Exception):
            make_company(payer_id="UNIQUE-001")

    def test_insurance_plan_links_to_company(self):
        co = make_company()
        plan = make_plan(co)
        self.assertEqual(plan.company_id, co.id)
        self.assertEqual(plan.plan_type, "ppo")

    def test_insurance_member_priority(self):
        co = make_company()
        plan = make_plan(co)
        pid = uuid.uuid4()
        primary = make_member(plan, patient_id=pid, priority_order=1)
        secondary_plan = make_plan(co, plan_code="SEC-001")
        secondary = make_member(secondary_plan, patient_id=pid, priority_order=2)
        self.assertEqual(primary.priority_order, 1)
        self.assertEqual(secondary.priority_order, 2)

    def test_coverage_creation(self):
        co = make_company()
        plan = make_plan(co)
        member = make_member(plan)
        cov = Coverage.objects.create(
            tenant_id=TENANT,
            insurance_member=member,
            coverage_type="medical",
            is_active=True,
            start_date=timezone.now().date(),
            deductible_individual=Decimal("500.00"),
            deductible_family=Decimal("1500.00"),
            out_of_pocket_individual=Decimal("2000.00"),
            out_of_pocket_family=Decimal("5000.00"),
        )
        self.assertEqual(cov.coverage_type, "medical")
        self.assertEqual(cov.deductible_individual, Decimal("500.00"))

    def test_benefit_linked_to_coverage(self):
        co = make_company()
        plan = make_plan(co)
        member = make_member(plan)
        cov = Coverage.objects.create(
            tenant_id=TENANT,
            insurance_member=member,
            coverage_type="medical",
            start_date=timezone.now().date(),
        )
        benefit = Benefit.objects.create(
            tenant_id=TENANT,
            coverage=cov,
            service_category="hospitalization",
            coverage_percentage=Decimal("90.00"),
            copay_amount=Decimal("50.00"),
            requires_preauth=True,
        )
        self.assertTrue(benefit.requires_preauth)
        self.assertEqual(benefit.coverage_percentage, Decimal("90.00"))

    def test_coverage_rule_types(self):
        co = make_company()
        plan = make_plan(co)
        rule = CoverageRule.objects.create(
            tenant_id=TENANT,
            insurance_plan=plan,
            rule_type="preauth_required",
            rule_description="All imaging requires preauthorization",
            is_active=True,
        )
        self.assertEqual(rule.rule_type, "preauth_required")

    def test_insurance_card_tracking(self):
        co = make_company()
        plan = make_plan(co)
        member = make_member(plan)
        card = InsuranceCard.objects.create(
            tenant_id=TENANT,
            insurance_member=member,
            issued_date=timezone.now().date(),
            is_current=True,
        )
        self.assertTrue(card.is_current)


# ─── Eligibility ──────────────────────────────────────────────────────────────


class EligibilityTest(TestCase):
    def setUp(self):
        self.co = make_company()
        self.plan = make_plan(self.co)
        self.patient_id = uuid.uuid4()
        self.member = make_member(self.plan, patient_id=self.patient_id)

    def test_eligibility_request_created(self):
        req = EligibilityRequest.objects.create(
            tenant_id=TENANT,
            patient_id=self.patient_id,
            insurance_plan_id=self.plan.id,
            service_date=timezone.now().date(),
            service_type="medical",
            request_type="real_time",
            status="pending",
        )
        self.assertEqual(req.status, "pending")
        self.assertEqual(req.service_type, "medical")

    def test_eligibility_response_linked(self):
        req = EligibilityRequest.objects.create(
            tenant_id=TENANT,
            patient_id=self.patient_id,
            insurance_plan_id=self.plan.id,
            service_date=timezone.now().date(),
            service_type="medical",
            request_type="real_time",
            status="received",
        )
        resp = EligibilityResponse.objects.create(
            tenant_id=TENANT,
            eligibility_request=req,
            is_eligible=True,
            coverage_status="active",
            coverage_start_date=timezone.now().date(),
            deductible_amount=Decimal("1000.00"),
            deductible_met=Decimal("250.00"),
            copay_amount=Decimal("30.00"),
            patient_responsibility_estimate=Decimal("80.00"),
        )
        self.assertTrue(resp.is_eligible)
        self.assertEqual(resp.coverage_status, "active")
        self.assertEqual(resp.patient_responsibility_estimate, Decimal("80.00"))

    def test_coverage_verification(self):
        verif = CoverageVerification.objects.create(
            tenant_id=TENANT,
            patient_id=self.patient_id,
            insurance_plan_id=self.plan.id,
            verified_at=timezone.now(),
            verification_method="electronic",
            coverage_confirmed=True,
        )
        self.assertTrue(verif.coverage_confirmed)

    def test_benefit_verification_links_to_coverage_verif(self):
        verif = CoverageVerification.objects.create(
            tenant_id=TENANT,
            patient_id=self.patient_id,
            insurance_plan_id=self.plan.id,
            verification_method="electronic",
        )
        bv = BenefitVerification.objects.create(
            tenant_id=TENANT,
            coverage_verification=verif,
            benefit_type="lab",
            is_covered=True,
            requires_preauth=False,
            coverage_percentage=Decimal("100.00"),
            network_status="in_network",
        )
        self.assertTrue(bv.is_covered)
        self.assertEqual(bv.network_status, "in_network")


# ─── Preauthorization ─────────────────────────────────────────────────────────


class PreauthorizationTest(TestCase):
    def setUp(self):
        self.co = make_company()
        self.plan = make_plan(self.co)
        self.patient_id = uuid.uuid4()
        self.provider_id = uuid.uuid4()

    def test_preauth_draft_creation(self):
        auth = Preauthorization.objects.create(
            tenant_id=TENANT,
            patient_id=self.patient_id,
            insurance_member_id=uuid.uuid4(),
            insurance_plan_id=self.plan.id,
            authorization_type="imaging",
            service_description="MRI Brain with contrast",
            icd11_diagnosis_codes=["8A00.0"],
            requested_units=1,
            requested_start_date=timezone.now().date(),
            status="draft",
            priority="routine",
            requesting_provider_id=self.provider_id,
            source_module="cymed_imaging",
        )
        self.assertEqual(auth.status, "draft")
        self.assertEqual(auth.authorization_type, "imaging")

    def test_preauth_submission_request(self):
        auth = Preauthorization.objects.create(
            tenant_id=TENANT,
            patient_id=self.patient_id,
            insurance_member_id=uuid.uuid4(),
            insurance_plan_id=self.plan.id,
            authorization_type="procedure",
            service_description="Laparoscopic Cholecystectomy",
            icd11_diagnosis_codes=["DC24"],
            requested_units=1,
            requested_start_date=timezone.now().date(),
            status="submitted",
            priority="routine",
            requesting_provider_id=self.provider_id,
        )
        req = AuthorizationRequest.objects.create(
            tenant_id=TENANT,
            preauthorization=auth,
            submitted_by_user_id=self.provider_id,
            clinical_notes="Patient has symptomatic cholelithiasis.",
            submission_method="electronic",
        )
        self.assertEqual(req.preauthorization_id, auth.id)
        self.assertEqual(req.submission_method, "electronic")

    def test_authorization_decision_approved(self):
        auth = Preauthorization.objects.create(
            tenant_id=TENANT,
            patient_id=self.patient_id,
            insurance_member_id=uuid.uuid4(),
            insurance_plan_id=self.plan.id,
            authorization_type="hospitalization",
            service_description="Elective admission",
            icd11_diagnosis_codes=["DC24"],
            requested_units=3,
            requested_start_date=timezone.now().date(),
            status="approved",
            priority="routine",
            requesting_provider_id=self.provider_id,
            auth_number="AUTH-2024-001",
            approved_units=3,
        )
        decision = AuthorizationDecision.objects.create(
            tenant_id=TENANT,
            preauthorization=auth,
            decision="approved",
            decision_date=timezone.now(),
            effective_date=timezone.now().date(),
        )
        self.assertEqual(decision.decision, "approved")
        self.assertEqual(auth.auth_number, "AUTH-2024-001")

    def test_authorization_appeal_filed(self):
        auth = Preauthorization.objects.create(
            tenant_id=TENANT,
            patient_id=self.patient_id,
            insurance_member_id=uuid.uuid4(),
            insurance_plan_id=self.plan.id,
            authorization_type="medication",
            service_description="Biologic therapy",
            icd11_diagnosis_codes=["FA20"],
            requested_units=4,
            requested_start_date=timezone.now().date(),
            status="denied",
            priority="routine",
            requesting_provider_id=self.provider_id,
        )
        appeal = AuthorizationAppeal.objects.create(
            tenant_id=TENANT,
            preauthorization=auth,
            submitted_by_user_id=self.provider_id,
            appeal_reason="Clinical necessity supported by peer-reviewed evidence.",
            appeal_level=1,
            status="submitted",
        )
        self.assertEqual(appeal.appeal_level, 1)
        self.assertEqual(appeal.status, "submitted")


# ─── Charge Capture ───────────────────────────────────────────────────────────


class ChargeCaptureTest(TestCase):
    def setUp(self):
        self.patient_id = uuid.uuid4()
        self.encounter_id = uuid.uuid4()
        self.facility_id = uuid.uuid4()

    def test_charge_created_from_lab_order(self):
        charge = Charge.objects.create(
            tenant_id=TENANT,
            patient_id=self.patient_id,
            encounter_id=self.encounter_id,
            charge_date=timezone.now().date(),
            service_source="laboratory",
            charge_category="lab_test",
            service_code="LAB-HBA1C",
            service_description="HbA1c Test",
            quantity=Decimal("1"),
            unit_price=Decimal("150.00"),
            total_amount=Decimal("150.00"),
            status="pending",
            is_billable=True,
            facility_id=self.facility_id,
        )
        self.assertEqual(charge.status, "pending")
        self.assertEqual(charge.total_amount, Decimal("150.00"))
        self.assertEqual(charge.service_source, "laboratory")

    def test_charge_auto_generation_from_admission(self):
        charge = Charge.objects.create(
            tenant_id=TENANT,
            patient_id=self.patient_id,
            encounter_id=self.encounter_id,
            charge_date=timezone.now().date(),
            service_source="hospital",
            charge_category="admission",
            service_code="ADM-WARD",
            service_description="Ward Admission Fee",
            quantity=Decimal("1"),
            unit_price=Decimal("500.00"),
            total_amount=Decimal("500.00"),
            status="approved",
            is_billable=True,
            facility_id=self.facility_id,
            source_module="cymed_hospital",
        )
        self.assertEqual(charge.charge_category, "admission")
        self.assertEqual(charge.source_module, "cymed_hospital")

    def test_charge_item_breakdown(self):
        charge = Charge.objects.create(
            tenant_id=TENANT,
            patient_id=self.patient_id,
            encounter_id=self.encounter_id,
            charge_date=timezone.now().date(),
            service_source="or",
            charge_category="procedure",
            service_code="SURG-CHOL",
            service_description="Laparoscopic Cholecystectomy",
            quantity=Decimal("1"),
            unit_price=Decimal("5000.00"),
            total_amount=Decimal("5000.00"),
            status="pending",
            facility_id=self.facility_id,
        )
        item = ChargeItem.objects.create(
            tenant_id=TENANT,
            charge=charge,
            item_code="SURG-INSTRUMENT",
            item_description="Surgical instruments",
            quantity=Decimal("1"),
            unit_cost=Decimal("800.00"),
            total_cost=Decimal("800.00"),
        )
        self.assertEqual(item.charge_id, charge.id)

    def test_charge_rule_creation(self):
        rule = ChargeRule.objects.create(
            tenant_id=TENANT,
            rule_name="Auto-charge on lab result verification",
            service_source="laboratory",
            charge_category="lab_test",
            auto_generate=True,
            trigger_event="lab_result_verified",
            service_code_map={"lab_result_verified": "LAB-AUTO"},
            multiplier=Decimal("1.0000"),
            is_active=True,
        )
        self.assertTrue(rule.auto_generate)
        self.assertEqual(rule.trigger_event, "lab_result_verified")

    def test_charge_void_audit_trail(self):
        charge = Charge.objects.create(
            tenant_id=TENANT,
            patient_id=self.patient_id,
            encounter_id=self.encounter_id,
            charge_date=timezone.now().date(),
            service_source="clinic",
            charge_category="consultation",
            service_code="CONS-GP",
            service_description="GP Consultation",
            quantity=Decimal("1"),
            unit_price=Decimal("200.00"),
            total_amount=Decimal("200.00"),
            status="voided",
            facility_id=self.facility_id,
        )
        audit = ChargeAudit.objects.create(
            tenant_id=TENANT,
            charge=charge,
            action="voided",
            performed_by_user_id=uuid.uuid4(),
            previous_status="approved",
            new_status="voided",
            notes="Duplicate charge",
        )
        self.assertEqual(audit.action, "voided")
        self.assertEqual(audit.new_status, "voided")
