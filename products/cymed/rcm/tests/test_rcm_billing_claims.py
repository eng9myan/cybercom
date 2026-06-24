"""
Tests for CyMed RCM — Billing, Claims, Denials, Collections.
"""
import uuid
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from products.cymed.rcm.billing.models import (
    PatientAccount, EncounterBilling, Invoice, InvoiceLine, BillingAdjustment, Refund,
)
from products.cymed.rcm.claims.models import (
    Claim, ClaimLine, ClaimSubmission, ClaimResponse, ClaimStatus, ClaimAttachment,
)
from products.cymed.rcm.denials.models import (
    Denial, DenialReason, Appeal, AppealOutcome, CorrectiveAction,
)
from products.cymed.rcm.collections.models import (
    CollectionCase, CollectionAction, PaymentPlan, CollectionOutcome,
)


TENANT = uuid.uuid4()


def make_patient_account(**kwargs):
    defaults = dict(
        tenant_id=TENANT,
        patient_id=uuid.uuid4(),
        account_number=f"ACC-{uuid.uuid4().hex[:8].upper()}",
        account_status="active",
        guarantor_type="self",
        credit_balance=Decimal("0"),
        outstanding_balance=Decimal("0"),
    )
    defaults.update(kwargs)
    return PatientAccount.objects.create(**defaults)


def make_encounter_billing(account, **kwargs):
    defaults = dict(
        tenant_id=TENANT,
        patient_account=account,
        encounter_id=uuid.uuid4(),
        encounter_type="outpatient",
        encounter_date=timezone.now().date(),
        facility_id=uuid.uuid4(),
        attending_provider_id=uuid.uuid4(),
        billing_status="open",
        total_charges=Decimal("500.00"),
        insurance_expected=Decimal("400.00"),
        patient_responsibility=Decimal("100.00"),
        amount_paid=Decimal("0"),
        balance_due=Decimal("500.00"),
    )
    defaults.update(kwargs)
    return EncounterBilling.objects.create(**defaults)


def make_invoice(account, enc=None, **kwargs):
    defaults = dict(
        tenant_id=TENANT,
        patient_account=account,
        encounter_billing=enc,
        invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
        invoice_type="insurance",
        invoice_date=timezone.now().date(),
        due_date=timezone.now().date(),
        billing_party_type="insurance",
        status="draft",
        amount_subtotal=Decimal("500.00"),
        amount_tax=Decimal("75.00"),
        amount_discount=Decimal("0"),
        amount_total=Decimal("575.00"),
        amount_paid=Decimal("0"),
        amount_outstanding=Decimal("575.00"),
        currency="SAR",
    )
    defaults.update(kwargs)
    return Invoice.objects.create(**defaults)


def make_claim(patient_account, **kwargs):
    defaults = dict(
        tenant_id=TENANT,
        claim_number=f"CLM-{uuid.uuid4().hex[:8].upper()}",
        patient_id=patient_account.patient_id,
        insurance_member_id=uuid.uuid4(),
        insurance_plan_id=uuid.uuid4(),
        encounter_billing_id=uuid.uuid4(),
        claim_type="professional",
        claim_date=timezone.now().date(),
        service_from_date=timezone.now().date(),
        service_to_date=timezone.now().date(),
        facility_id=uuid.uuid4(),
        rendering_provider_id=uuid.uuid4(),
        status="draft",
        total_billed_amount=Decimal("500.00"),
        total_approved_amount=Decimal("0"),
        total_paid_amount=Decimal("0"),
        patient_responsibility=Decimal("100.00"),
    )
    defaults.update(kwargs)
    return Claim.objects.create(**defaults)


# ─── Billing ──────────────────────────────────────────────────────────────────

class PatientAccountTest(TestCase):
    def test_patient_account_creation(self):
        acct = make_patient_account()
        self.assertEqual(acct.account_status, "active")
        self.assertEqual(acct.guarantor_type, "self")

    def test_account_number_unique(self):
        make_patient_account(account_number="ACC-UNIQUE-001")
        with self.assertRaises(Exception):
            make_patient_account(account_number="ACC-UNIQUE-001")

    def test_encounter_billing_status_flow(self):
        acct = make_patient_account()
        enc = make_encounter_billing(acct)
        self.assertEqual(enc.billing_status, "open")
        enc.billing_status = "billed"
        enc.save()
        enc.refresh_from_db()
        self.assertEqual(enc.billing_status, "billed")

    def test_invoice_creation(self):
        acct = make_patient_account()
        enc = make_encounter_billing(acct)
        inv = make_invoice(acct, enc=enc)
        self.assertEqual(inv.status, "draft")
        self.assertEqual(inv.amount_total, Decimal("575.00"))
        self.assertEqual(inv.currency, "SAR")

    def test_invoice_line_added(self):
        acct = make_patient_account()
        inv = make_invoice(acct)
        line = InvoiceLine.objects.create(
            tenant_id=TENANT,
            invoice=inv,
            line_number=1,
            service_date=timezone.now().date(),
            service_code="CONS-GP",
            service_description="GP Consultation",
            quantity=Decimal("1"),
            unit_price=Decimal("200.00"),
            discount_percentage=Decimal("0"),
            discount_amount=Decimal("0"),
            line_total=Decimal("200.00"),
            tax_amount=Decimal("30.00"),
        )
        self.assertEqual(line.service_code, "CONS-GP")
        self.assertEqual(line.line_total, Decimal("200.00"))

    def test_billing_adjustment_contractual(self):
        acct = make_patient_account()
        inv = make_invoice(acct)
        adj = BillingAdjustment.objects.create(
            tenant_id=TENANT,
            invoice=inv,
            adjustment_type="contractual",
            adjustment_amount=Decimal("100.00"),
            reason="Contractual write-off per payer agreement",
        )
        self.assertEqual(adj.adjustment_type, "contractual")
        self.assertEqual(adj.adjustment_amount, Decimal("100.00"))

    def test_refund_processing(self):
        acct = make_patient_account()
        inv = make_invoice(acct, amount_paid=Decimal("575.00"), amount_outstanding=Decimal("0"), status="paid")
        refund = Refund.objects.create(
            tenant_id=TENANT,
            invoice=inv,
            refund_amount=Decimal("50.00"),
            refund_method="bank_transfer",
            refund_date=timezone.now().date(),
            reason="Overpayment refund",
            processed_by_user_id=uuid.uuid4(),
            status="pending",
        )
        self.assertEqual(refund.status, "pending")
        self.assertEqual(refund.refund_method, "bank_transfer")


# ─── Claims ───────────────────────────────────────────────────────────────────

class ClaimsTest(TestCase):
    def setUp(self):
        self.acct = make_patient_account()

    def test_claim_creation(self):
        claim = make_claim(self.acct)
        self.assertEqual(claim.status, "draft")
        self.assertEqual(claim.claim_type, "professional")
        self.assertFalse(claim.is_resubmission)

    def test_claim_with_diagnosis_codes(self):
        claim = make_claim(
            self.acct,
            icd11_primary_diagnosis="BA80",
            icd11_secondary_diagnoses=["5A10", "CA40"],
        )
        self.assertEqual(claim.icd11_primary_diagnosis, "BA80")
        self.assertIn("5A10", claim.icd11_secondary_diagnoses)

    def test_claim_line_items(self):
        claim = make_claim(self.acct)
        line = ClaimLine.objects.create(
            tenant_id=TENANT,
            claim=claim,
            line_number=1,
            service_date=timezone.now().date(),
            service_code="99213",
            service_description="Office visit established patient",
            quantity=Decimal("1"),
            unit_charge=Decimal("300.00"),
            line_charge=Decimal("300.00"),
            approved_amount=Decimal("0"),
            paid_amount=Decimal("0"),
            line_status="included",
        )
        self.assertEqual(line.line_status, "included")
        self.assertEqual(line.line_charge, Decimal("300.00"))

    def test_claim_submission_tracking(self):
        claim = make_claim(self.acct, status="submitted")
        submission = ClaimSubmission.objects.create(
            tenant_id=TENANT,
            claim=claim,
            submitted_by_user_id=uuid.uuid4(),
            submission_method="electronic",
            payer_transaction_id="TXN-123456",
        )
        self.assertFalse(submission.acknowledgement_received)
        self.assertEqual(submission.submission_method, "electronic")

    def test_claim_response_payment(self):
        claim = make_claim(self.acct, status="paid", total_paid_amount=Decimal("400.00"))
        response = ClaimResponse.objects.create(
            tenant_id=TENANT,
            claim=claim,
            response_date=timezone.now(),
            response_type="payment",
            approved_amount=Decimal("450.00"),
            paid_amount=Decimal("400.00"),
            payment_date=timezone.now().date(),
            payment_method="eft",
            eob_number="EOB-2024-001",
        )
        self.assertEqual(response.response_type, "payment")
        self.assertEqual(response.paid_amount, Decimal("400.00"))

    def test_claim_status_history(self):
        claim = make_claim(self.acct)
        entry = ClaimStatus.objects.create(
            tenant_id=TENANT,
            claim=claim,
            previous_status="draft",
            new_status="submitted",
            changed_by_user_id=uuid.uuid4(),
        )
        self.assertEqual(entry.new_status, "submitted")

    def test_claim_resubmission(self):
        original = make_claim(self.acct, status="denied")
        resubmit = make_claim(
            self.acct,
            status="submitted",
            is_resubmission=True,
            original_claim_id=original.id,
        )
        self.assertTrue(resubmit.is_resubmission)
        self.assertEqual(resubmit.original_claim_id, original.id)


# ─── Denials ──────────────────────────────────────────────────────────────────

class DenialsTest(TestCase):
    def setUp(self):
        self.acct = make_patient_account()
        self.claim = make_claim(self.acct, status="denied")

    def test_denial_creation(self):
        denial = Denial.objects.create(
            tenant_id=TENANT,
            claim_id=self.claim.id,
            patient_id=self.acct.patient_id,
            insurance_plan_id=uuid.uuid4(),
            denial_date=timezone.now().date(),
            denial_code="AUTH001",
            denial_category="authorization",
            denial_description="Prior authorization required",
            denial_amount=Decimal("400.00"),
            status="open",
            root_cause="missing_auth",
        )
        self.assertEqual(denial.status, "open")
        self.assertEqual(denial.denial_category, "authorization")

    def test_denial_reason_library(self):
        reason = DenialReason.objects.create(
            tenant_id=TENANT,
            denial_code="AUTH001",
            description="Prior authorization not obtained",
            category="authorization",
            common_resolution="Obtain retroactive authorization or appeal with clinical justification",
            is_active=True,
        )
        self.assertEqual(reason.denial_code, "AUTH001")

    def test_appeal_filed(self):
        denial = Denial.objects.create(
            tenant_id=TENANT,
            claim_id=self.claim.id,
            patient_id=self.acct.patient_id,
            insurance_plan_id=uuid.uuid4(),
            denial_date=timezone.now().date(),
            denial_code="MED001",
            denial_category="medical_necessity",
            denial_description="Not medically necessary",
            denial_amount=Decimal("3000.00"),
            status="in_review",
        )
        appeal = Appeal.objects.create(
            tenant_id=TENANT,
            denial=denial,
            appeal_level=1,
            appeal_date=timezone.now().date(),
            submitted_by_user_id=uuid.uuid4(),
            appeal_type="internal",
            appeal_reason="Clinical evidence supports medical necessity per CPG",
            status="submitted",
        )
        self.assertEqual(appeal.status, "submitted")
        self.assertEqual(appeal.appeal_type, "internal")

    def test_corrective_action_assigned(self):
        denial = Denial.objects.create(
            tenant_id=TENANT,
            claim_id=self.claim.id,
            patient_id=self.acct.patient_id,
            insurance_plan_id=uuid.uuid4(),
            denial_date=timezone.now().date(),
            denial_code="COD001",
            denial_category="coding",
            denial_description="Invalid diagnosis code",
            denial_amount=Decimal("200.00"),
            status="in_review",
        )
        action = CorrectiveAction.objects.create(
            tenant_id=TENANT,
            denial=denial,
            action_type="recode",
            description="Recode with correct ICD-11 code",
            assigned_to_user_id=uuid.uuid4(),
            due_date=timezone.now().date(),
            status="pending",
        )
        self.assertEqual(action.action_type, "recode")


# ─── Collections ──────────────────────────────────────────────────────────────

class CollectionsTest(TestCase):
    def setUp(self):
        self.acct = make_patient_account(outstanding_balance=Decimal("2500.00"))

    def test_collection_case_creation(self):
        case = CollectionCase.objects.create(
            tenant_id=TENANT,
            patient_id=self.acct.patient_id,
            patient_account_id=self.acct.id,
            case_number=f"COL-{uuid.uuid4().hex[:8].upper()}",
            outstanding_balance=Decimal("2500.00"),
            original_balance=Decimal("2500.00"),
            aging_bucket="60_days",
            status="active",
            priority="high",
        )
        self.assertEqual(case.aging_bucket, "60_days")
        self.assertEqual(case.outstanding_balance, Decimal("2500.00"))

    def test_collection_action_logged(self):
        case = CollectionCase.objects.create(
            tenant_id=TENANT,
            patient_id=self.acct.patient_id,
            patient_account_id=self.acct.id,
            case_number=f"COL-{uuid.uuid4().hex[:8].upper()}",
            outstanding_balance=Decimal("2500.00"),
            original_balance=Decimal("2500.00"),
            aging_bucket="30_days",
            status="active",
            priority="medium",
        )
        action = CollectionAction.objects.create(
            tenant_id=TENANT,
            collection_case=case,
            action_type="phone_call",
            performed_by_user_id=uuid.uuid4(),
            notes="Patient agreed to partial payment",
            amount_collected=Decimal("500.00"),
        )
        self.assertEqual(action.action_type, "phone_call")
        self.assertEqual(action.amount_collected, Decimal("500.00"))

    def test_payment_plan_created(self):
        case = CollectionCase.objects.create(
            tenant_id=TENANT,
            patient_id=self.acct.patient_id,
            patient_account_id=self.acct.id,
            case_number=f"COL-{uuid.uuid4().hex[:8].upper()}",
            outstanding_balance=Decimal("2500.00"),
            original_balance=Decimal("2500.00"),
            aging_bucket="60_days",
            status="payment_plan",
            priority="medium",
        )
        plan = PaymentPlan.objects.create(
            tenant_id=TENANT,
            collection_case=case,
            total_amount=Decimal("2500.00"),
            installment_amount=Decimal("500.00"),
            frequency="monthly",
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            number_of_installments=5,
            amount_paid=Decimal("0"),
            amount_remaining=Decimal("2500.00"),
            status="active",
        )
        self.assertEqual(plan.number_of_installments, 5)
        self.assertEqual(plan.frequency, "monthly")

    def test_collection_resolved(self):
        case = CollectionCase.objects.create(
            tenant_id=TENANT,
            patient_id=self.acct.patient_id,
            patient_account_id=self.acct.id,
            case_number=f"COL-{uuid.uuid4().hex[:8].upper()}",
            outstanding_balance=Decimal("0"),
            original_balance=Decimal("1000.00"),
            aging_bucket="current",
            status="resolved",
            priority="low",
        )
        outcome = CollectionOutcome.objects.create(
            tenant_id=TENANT,
            collection_case=case,
            outcome_date=timezone.now().date(),
            outcome_type="paid_in_full",
            amount_recovered=Decimal("1000.00"),
            amount_written_off=Decimal("0"),
        )
        self.assertEqual(outcome.outcome_type, "paid_in_full")
