import uuid
import pytest
from django.utils import timezone
from django.db import transaction

from products.cymed.core.patients.models import Patient
from products.cymed.core.encounters.models import Encounter
from products.cymed.core.organizations.models import Organization
from products.cymed.core.facilities.models import Facility, Department, Ward, Room, Bed

from products.cymed.rcm.billing.models import PatientAccount, EncounterBilling, Invoice, InvoiceLine
from products.cymed.rcm.claims.models import Claim, ClaimLine, ClaimSubmission, ClaimResponse
from products.cymed.rcm.denials.models import Denial, DenialReason, Appeal, AppealOutcome
from products.cymed.rcm.eligibility.models import EligibilityRequest, EligibilityResponse
from products.cymed.rcm.preauthorization.models import Preauthorization
from products.cymed.rcm.insurance.models import InsuranceCompany, InsurancePlan, InsuranceMember
from platform.events.models import OutboxEvent

from products.cymed.rcm.services import (
    EligibilityService, BillingService, ClaimsService, PreAuthService, DenialService, CollectionService, RevenueAnalyticsService
)


@pytest.fixture
def test_tenant_id():
    return uuid.uuid4()


@pytest.fixture
def setup_rcm_base_data(test_tenant_id):
    org = Organization.objects.create(
        tenant_id=test_tenant_id, name="Hospital Org", slug="hosp-org", organization_type="hospital"
    )
    facility = Facility.objects.create(
        tenant_id=test_tenant_id, organization=org, name="Main Hospital Facility", code="MAIN-HOSP"
    )
    patient = Patient.objects.create(
        tenant_id=test_tenant_id, first_name="Mariam", last_name="Al-Rashid", dob="1990-08-20", mrn="MRN-RCM-001"
    )
    encounter = Encounter.objects.create(
        tenant_id=test_tenant_id, patient=patient, encounter_type="inpatient",
        status="in_progress", organization=org, facility=facility
    )
    
    # Create Payer and Plan
    company = InsuranceCompany.objects.create(
        tenant_id=test_tenant_id, name="Bupa Arabia", short_name="Bupa", payer_id="PAYER-BUPA", company_type="private"
    )
    plan = InsurancePlan.objects.create(
        tenant_id=test_tenant_id, company=company, plan_name="Premium Corporate", plan_code="BUPA-PREM", plan_type="corporate", network_type="in_network", coverage_category="premium"
    )
    member = InsuranceMember.objects.create(
        tenant_id=test_tenant_id, patient_id=patient.id, insurance_plan=plan, member_id="MEM-84729", member_relationship="self", effective_date=timezone.now().date()
    )

    # Link primary member ID
    acc_num = f"ACC-{patient.mrn}"
    account = PatientAccount.objects.create(
        tenant_id=test_tenant_id,
        patient_id=patient.id,
        account_number=acc_num,
        primary_insurance_member_id=member.id,
        account_status="active"
    )

    return {
        "org": org,
        "facility": facility,
        "patient": patient,
        "encounter": encounter,
        "company": company,
        "plan": plan,
        "member": member,
        "account": account,
    }


@pytest.mark.django_db
class TestRCMEndToEndWorkflow:

    def test_full_revenue_cycle_encounter_to_payment(self, test_tenant_id, setup_rcm_base_data):
        patient = setup_rcm_base_data["patient"]
        encounter = setup_rcm_base_data["encounter"]
        company = setup_rcm_base_data["company"]
        account = setup_rcm_base_data["account"]

        # 1. Eligibility Check
        el_res = EligibilityService.check_eligibility(
            tenant_id=str(test_tenant_id),
            patient_id=str(patient.id),
            payer_id=str(company.id),
            service_date=timezone.now().date(),
        )
        assert el_res["eligible"] is True
        assert el_res["coverage_status"] == "active"

        # 2. Prior Auth Submission
        auth_res = PreAuthService.submit_prior_auth(
            tenant_id=str(test_tenant_id),
            encounter_id=str(encounter.id),
            payer_id=str(company.id),
            service_code="99214",
        )
        assert auth_res["preauth_id"] is not None

        # 3. Capture charges
        charge_res = BillingService.capture_charge(
            tenant_id=str(test_tenant_id),
            encounter_id=str(encounter.id),
            patient_id=str(patient.id),
            cpt_code="99214",
            icd_codes=["E11.9"],
            units=1,
            facility_id=str(setup_rcm_base_data["facility"].id),
        )
        assert charge_res["encounter_billing_id"] is not None

        # 4. Generate Invoice
        inv_res = BillingService.generate_invoice(
            tenant_id=str(test_tenant_id),
            patient_account_id=str(account.id),
            encounter_billing_id=charge_res["encounter_billing_id"],
        )
        assert inv_res["invoice_id"] is not None
        assert inv_res["invoice_number"] is not None

        # 5. Create Claim
        claim_res = ClaimsService.create_claim(
            tenant_id=str(test_tenant_id),
            encounter_billing_id=charge_res["encounter_billing_id"],
            payer_id=str(company.id),
        )
        assert claim_res["claim_id"] is not None

        # 6. Submit Claim
        sub_res = ClaimsService.submit_claim(
            tenant_id=str(test_tenant_id),
            claim_id=claim_res["claim_id"],
        )
        assert sub_res["submission_id"] is not None

        # 7. Process ERA with denial
        era_data = {
            "approved_amount": 80.00,
            "paid_amount": 80.00,  # paid 80 out of 110 (30 denied/patient portion)
        }
        remit_res = ClaimsService.process_remittance(
            tenant_id=str(test_tenant_id),
            claim_id=claim_res["claim_id"],
            era_data=era_data,
        )
        assert remit_res["denied_amount"] > 0

        # Verify denial was created
        denial = Denial.objects.filter(claim_id=claim_res["claim_id"], tenant_id=test_tenant_id).first()
        assert denial is not None
        assert denial.status == "open"

        # 8. Submit Appeal
        appeal_res = DenialService.submit_appeal(
            tenant_id=str(test_tenant_id),
            denial_id=str(denial.id),
            appeal_type="administrative",
            clinical_summary="Authorization retroactively obtained.",
            submitted_by=str(uuid.uuid4()),
        )
        assert appeal_res["appeal_id"] is not None

        # 9. Record Appeal Outcome (Overturned/Approved)
        outcome_res = DenialService.record_appeal_outcome(
            tenant_id=str(test_tenant_id),
            appeal_id=appeal_res["appeal_id"],
            outcome="approved",
            amount_recovered=30.00,
        )
        assert outcome_res["outcome"] == "approved"

        # 10. Patient pays remaining balance
        pay_res = BillingService.post_payment(
            tenant_id=str(test_tenant_id),
            invoice_id=inv_res["invoice_id"],
            amount=25.00,  # copay
            payment_method="credit_card",
        )
        assert pay_res["outstanding_balance"] >= 0.00

    def test_claim_denial_appeal_recovery(self, test_tenant_id, setup_rcm_base_data):
        patient = setup_rcm_base_data["patient"]
        encounter = setup_rcm_base_data["encounter"]
        company = setup_rcm_base_data["company"]
        account = setup_rcm_base_data["account"]

        # Capture and invoice
        charge = BillingService.capture_charge(
            tenant_id=str(test_tenant_id),
            encounter_id=str(encounter.id),
            patient_id=str(patient.id),
            cpt_code="99214",
            icd_codes=["E11.9"],
            facility_id=str(setup_rcm_base_data["facility"].id),
        )
        BillingService.generate_invoice(
            tenant_id=str(test_tenant_id),
            patient_account_id=str(account.id),
            encounter_billing_id=charge["encounter_billing_id"],
        )
        claim = ClaimsService.create_claim(
            tenant_id=str(test_tenant_id),
            encounter_billing_id=charge["encounter_billing_id"],
            payer_id=str(company.id),
        )

        # Trigger denial
        denial_res = DenialService.create_denial(
            tenant_id=str(test_tenant_id),
            claim_id=claim["claim_id"],
            denial_reason_code="MISSING_AUTH",
            denial_description="Auth was missing",
            payer_id=str(company.id),
        )
        assert denial_res["denial_id"] is not None

        # Appeal
        appeal = DenialService.submit_appeal(
            tenant_id=str(test_tenant_id),
            denial_id=denial_res["denial_id"],
            appeal_type="internal",
            clinical_summary="Retroactive auth",
            submitted_by=str(uuid.uuid4()),
        )
        assert appeal["appeal_id"] is not None

    def test_ar_aging_calculation(self, test_tenant_id):
        # Verify dashboard reports aging buckets correctly
        dashboard = RevenueAnalyticsService.get_ar_dashboard(tenant_id=str(test_tenant_id))
        assert "ar_by_age" in dashboard
        assert len(dashboard["ar_by_age"]) == 5

    def test_collection_case_workflow(self, test_tenant_id, setup_rcm_base_data):
        account = setup_rcm_base_data["account"]
        # Create case
        case = CollectionService.create_collection_case(
            tenant_id=str(test_tenant_id),
            patient_account_id=str(account.id),
            outstanding_balance=1500.00,
            days_outstanding=95,
        )
        assert case["case_id"] is not None

        # Add Action
        act = CollectionService.add_collection_action(
            tenant_id=str(test_tenant_id),
            case_id=case["case_id"],
            action_type="phone_call",
            performed_by=str(uuid.uuid4()),
            notes="Called patient, left voicemail."
        )
        assert act["action_id"] is not None

        # Create Payment Plan
        plan = CollectionService.create_payment_plan(
            tenant_id=str(test_tenant_id),
            case_id=case["case_id"],
            plan_type="installment",
            installment_amount=125.00,
            installment_frequency="monthly",
            start_date=timezone.now().date(),
        )
        assert plan["payment_plan_id"] is not None

        # Resolve Case
        res = CollectionService.record_collection_outcome(
            tenant_id=str(test_tenant_id),
            case_id=case["case_id"],
            outcome_type="full_payment",
        )
        assert res["status"] == "resolved"
