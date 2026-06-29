"""
CyMed Patient Portal — Clinical Integration Tests (Phase 3.6)
Covers: laboratory_results, imaging_results, prescriptions,
        health_journey, payments, insurance, wallet
Target coverage: 90%+
"""

import uuid
from datetime import date, timedelta

import pytest
from django.utils import timezone

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
ACCOUNT = uuid.uuid4()
OTHER_TENANT = uuid.uuid4()


# ──────────────────────────────────────────────────
# LABORATORY RESULTS TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestLabResults:
    def test_create_lab_result_view(self):
        from products.cymed.patient_portal.laboratory_results.models import LabResultView

        result = LabResultView.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            cymed_lab_result_id=uuid.uuid4(),
            lab_id=uuid.uuid4(),
            lab_name="Alpha Diagnostics",
            test_name="Complete Blood Count (CBC)",
            loinc_code="58410-2",
            result_status="final",
            is_critical=False,
        )
        assert result.test_name == "Complete Blood Count (CBC)"
        assert result.result_status == "final"
        assert result.is_viewed is False

    def test_critical_lab_result(self):
        from products.cymed.patient_portal.laboratory_results.models import LabResultView

        result = LabResultView.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            cymed_lab_result_id=uuid.uuid4(),
            lab_id=uuid.uuid4(),
            lab_name="City Lab",
            test_name="Potassium",
            loinc_code="2823-3",
            result_status="final",
            is_critical=True,
        )
        assert result.is_critical is True

    def test_critical_result_acknowledgement(self):
        from products.cymed.patient_portal.laboratory_results.models import (
            CriticalResultAcknowledgement,
            LabResultView,
        )

        result = LabResultView.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            cymed_lab_result_id=uuid.uuid4(),
            lab_id=uuid.uuid4(),
            lab_name="City Lab",
            test_name="Sodium",
            result_status="final",
            is_critical=True,
        )
        ack = CriticalResultAcknowledgement.objects.create(
            tenant_id=TENANT,
            lab_result=result,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            action_taken="contacted_provider",
            notes="Called Dr. Smith immediately.",
        )
        assert ack.action_taken == "contacted_provider"
        assert result.acknowledgements.count() == 1

    def test_lab_result_trend(self):
        from products.cymed.patient_portal.laboratory_results.models import LabResultTrend

        trend = LabResultTrend.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            test_code="2345-7",
            test_name="HbA1c",
            loinc_code="4548-4",
            unit="%",
            reference_range_low=4.0,
            reference_range_high=5.7,
            datapoints=[
                {"date": "2025-01-01", "value": 7.2},
                {"date": "2025-04-01", "value": 6.8},
                {"date": "2025-07-01", "value": 6.4},
            ],
        )
        assert trend.test_name == "HbA1c"
        assert len(trend.datapoints) == 3

    def test_lab_share_link(self):
        from products.cymed.patient_portal.laboratory_results.models import (
            LabResultShareLink,
            LabResultView,
        )

        result = LabResultView.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            cymed_lab_result_id=uuid.uuid4(),
            lab_id=uuid.uuid4(),
            lab_name="Test Lab",
            test_name="Lipid Panel",
            result_status="final",
        )
        link = LabResultShareLink.objects.create(
            tenant_id=TENANT,
            lab_result=result,
            account_id=ACCOUNT,
            share_token="lab-share-tok-001",
            shared_with_name="Dr. Rashed",
            shared_with_email="rashed@hospital.com",
            valid_until=timezone.now() + timedelta(days=30),
        )
        assert link.is_revoked is False
        assert link.access_count == 0


# ──────────────────────────────────────────────────
# IMAGING RESULTS TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestImagingResults:
    def test_create_imaging_result_view(self):
        from products.cymed.patient_portal.imaging_results.models import ImagingResultView

        result = ImagingResultView.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            cymed_imaging_result_id=uuid.uuid4(),
            imaging_center_id=uuid.uuid4(),
            imaging_center_name="Premier Radiology",
            accession_number="ACC-2026-001",
            study_date=date.today() - timedelta(days=2),
            modality="MRI",
            body_part="Brain",
            report_status="final",
            radiologist_name="Dr. Alaa Radhi",
        )
        assert result.modality == "MRI"
        assert result.report_status == "final"
        assert result.is_viewed is False

    def test_imaging_study_metadata(self):
        from products.cymed.patient_portal.imaging_results.models import (
            ImagingResultView,
            ImagingStudyMetadata,
        )

        result = ImagingResultView.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            cymed_imaging_result_id=uuid.uuid4(),
            imaging_center_id=uuid.uuid4(),
            imaging_center_name="Test Center",
            modality="CT",
            report_status="final",
        )
        series = ImagingStudyMetadata.objects.create(
            tenant_id=TENANT,
            imaging_result=result,
            series_number=1,
            series_description="Axial T1",
            modality="MRI",
            instance_count=120,
        )
        assert series.instance_count == 120
        assert result.series.count() == 1

    def test_imaging_report_access(self):
        from products.cymed.patient_portal.imaging_results.models import (
            ImagingReportAccess,
            ImagingResultView,
        )

        result = ImagingResultView.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            cymed_imaging_result_id=uuid.uuid4(),
            imaging_center_id=uuid.uuid4(),
            imaging_center_name="Test Center",
            modality="X-Ray",
            report_status="final",
        )
        access = ImagingReportAccess.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            imaging_result=result,
            access_type="download_report",
        )
        assert access.access_type == "download_report"
        assert result.access_log.count() == 1

    def test_imaging_share_link(self):
        from products.cymed.patient_portal.imaging_results.models import (
            ImagingResultView,
            ImagingShareLink,
        )

        result = ImagingResultView.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            cymed_imaging_result_id=uuid.uuid4(),
            imaging_center_id=uuid.uuid4(),
            imaging_center_name="Test Center",
            modality="CT",
            report_status="final",
        )
        link = ImagingShareLink.objects.create(
            tenant_id=TENANT,
            imaging_result=result,
            account_id=ACCOUNT,
            share_token="img-share-001",
            share_type="images_and_report",
            valid_until=timezone.now() + timedelta(days=7),
        )
        assert link.share_type == "images_and_report"
        assert link.is_revoked is False


# ──────────────────────────────────────────────────
# PORTAL PRESCRIPTIONS TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestPortalPrescriptions:
    def test_portal_prescription_view(self):
        from products.cymed.patient_portal.prescriptions.models import PortalPrescriptionView

        rx = PortalPrescriptionView.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            cymed_prescription_id=uuid.uuid4(),
            prescription_number="RX-PORTAL-001",
            prescriber_name="Dr. Hassan",
            status="active",
            refills_authorized=3,
            refills_dispensed=1,
            can_request_refill=True,
            items_summary=[{"drug_name": "Metformin 500mg", "dose": "500mg", "frequency": "BID"}],
        )
        assert rx.status == "active"
        assert rx.can_request_refill is True
        assert rx.refills_dispensed == 1

    def test_refill_request(self):
        from products.cymed.patient_portal.prescriptions.models import (
            PortalPrescriptionView,
            RefillRequest,
        )

        rx = PortalPrescriptionView.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            cymed_prescription_id=uuid.uuid4(),
            prescription_number="RX-PORTAL-002",
            status="active",
            can_request_refill=True,
        )
        refill = RefillRequest.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            portal_prescription=rx,
            preferred_pharmacy_name="Health Pharmacy",
            pickup_method="delivery",
            delivery_address="123 Main St, Apt 4B",
            status="submitted",
        )
        assert refill.status == "submitted"
        assert refill.pickup_method == "delivery"
        assert rx.refill_requests.count() == 1

    def test_medication_instruction(self):
        from products.cymed.patient_portal.prescriptions.models import MedicationInstruction

        instr = MedicationInstruction.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            drug_code="RXN-12345",
            drug_name="Metformin 500mg",
            instruction_text="Take 1 tablet twice daily with meals.",
            instruction_text_ar="تناول قرصاً واحداً مرتين يومياً مع الوجبات.",
            dose="500mg",
            frequency="BID",
            route="oral",
            special_warnings=["Do not crush", "Take with food"],
        )
        assert instr.drug_name == "Metformin 500mg"
        assert "Do not crush" in instr.special_warnings

    def test_medication_adherence(self):
        from products.cymed.patient_portal.prescriptions.models import (
            MedicationAdherenceLog,
            PortalPrescriptionView,
        )

        rx = PortalPrescriptionView.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            cymed_prescription_id=uuid.uuid4(),
            prescription_number="RX-PORTAL-003",
            status="active",
        )
        log = MedicationAdherenceLog.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            portal_prescription=rx,
            drug_code="RXN-001",
            drug_name="Metformin 500mg",
            scheduled_time=timezone.now(),
            taken_at=timezone.now(),
            status="taken",
        )
        assert log.status == "taken"
        assert rx.adherence_logs.count() == 1


# ──────────────────────────────────────────────────
# HEALTH JOURNEY TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestHealthJourney:
    def test_health_timeline(self):
        from products.cymed.patient_portal.health_journey.models import HealthTimeline

        timeline = HealthTimeline.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
        )
        assert timeline.total_events == 0

    def test_timeline_events(self):
        from products.cymed.patient_portal.health_journey.models import (
            HealthTimeline,
            HealthTimelineEvent,
        )

        timeline = HealthTimeline.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
        )
        [
            HealthTimelineEvent.objects.create(
                tenant_id=TENANT,
                timeline=timeline,
                account_id=ACCOUNT,
                patient_id=PATIENT,
                event_type=etype,
                title=f"Event: {etype}",
                provider_name="Dr. Hassan",
                facility_name="City Hospital",
                event_date=date.today() - timedelta(days=i * 30),
            )
            for i, etype in enumerate(
                ["appointment", "lab_result", "prescription", "hospitalization"]
            )
        ]
        assert timeline.events.count() == 4

    def test_patient_journey(self):
        from products.cymed.patient_portal.health_journey.models import PatientJourney

        journey = PatientJourney.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            journey_name="Diabetes Management 2026",
            journey_type="chronic_condition",
            primary_diagnosis="Type 2 Diabetes Mellitus",
            icd11_code="5A11",
            start_date=date(2026, 1, 1),
            status="active",
            care_team=[
                {
                    "provider_id": str(uuid.uuid4()),
                    "provider_name": "Dr. Hassan",
                    "role": "Endocrinologist",
                }
            ],
        )
        assert journey.status == "active"
        assert journey.journey_type == "chronic_condition"

    def test_health_milestone(self):
        from products.cymed.patient_portal.health_journey.models import (
            HealthMilestone,
            PatientJourney,
        )

        journey = PatientJourney.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            journey_name="Cancer Journey",
            journey_type="cancer_care",
            start_date=date(2025, 6, 1),
            status="active",
        )
        m = HealthMilestone.objects.create(
            tenant_id=TENANT,
            journey=journey,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            title="First Chemotherapy Session",
            milestone_type="first_chemo",
            milestone_date=date(2025, 7, 1),
            is_achieved=True,
        )
        assert m.is_achieved is True
        assert journey.milestones.count() == 1

    def test_care_episode(self):
        from products.cymed.patient_portal.health_journey.models import CareEpisode

        episode = CareEpisode.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            episode_type="inpatient",
            facility_name="City General Hospital",
            facility_id=uuid.uuid4(),
            admission_date=date.today() - timedelta(days=10),
            discharge_date=date.today() - timedelta(days=5),
            primary_diagnosis="Appendicitis",
            attending_physician="Dr. Mohamed Khalil",
        )
        assert episode.episode_type == "inpatient"


# ──────────────────────────────────────────────────
# PAYMENTS TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestPayments:
    def test_patient_invoice(self):
        from products.cymed.patient_portal.payments.models import PatientInvoice

        invoice = PatientInvoice.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            cycom_invoice_id="INV-CYCOM-001",
            invoice_number="INV-PORTAL-001",
            invoice_type="consultation",
            provider_name="Al-Nour Clinic",
            amount_total=250.00,
            amount_covered_insurance=200.00,
            amount_patient_due=50.00,
            currency="USD",
            status="pending",
        )
        assert invoice.amount_patient_due == 50.00
        assert invoice.status == "pending"

    def test_payment_transaction(self):
        from products.cymed.patient_portal.payments.models import PatientInvoice, PaymentTransaction

        invoice = PatientInvoice.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            cycom_invoice_id="INV-CYCOM-002",
            invoice_number="INV-PORTAL-002",
            invoice_type="lab",
            provider_name="Alpha Lab",
            amount_total=75.00,
            amount_patient_due=75.00,
            currency="USD",
            status="pending",
        )
        txn = PaymentTransaction.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            invoice=invoice,
            transaction_reference="TXN-001-2026",
            payment_method="credit_card",
            payment_gateway="stripe",
            amount=75.00,
            currency="USD",
            status="completed",
            paid_at=timezone.now(),
        )
        assert txn.status == "completed"
        assert txn.amount == 75.00

    def test_payment_method(self):
        from products.cymed.patient_portal.payments.models import PaymentMethod

        pm = PaymentMethod.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            method_type="credit_card",
            display_name="Visa ending in 4242",
            last_four="4242",
            card_brand="Visa",
            expiry_month=12,
            expiry_year=2028,
            is_default=True,
            is_active=True,
        )
        assert pm.is_default is True
        assert pm.last_four == "4242"

    def test_installment_plan(self):
        from products.cymed.patient_portal.payments.models import InstallmentPlan, PatientInvoice

        invoice = PatientInvoice.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            cycom_invoice_id="INV-CYCOM-003",
            invoice_number="INV-PORTAL-003",
            invoice_type="admission",
            provider_name="City Hospital",
            amount_total=5000.00,
            amount_patient_due=1000.00,
            currency="USD",
            status="pending",
        )
        plan = InstallmentPlan.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            invoice=invoice,
            total_amount=1000.00,
            installment_count=4,
            installment_amount=250.00,
            first_payment_date=date.today() + timedelta(days=30),
            frequency="monthly",
            status="active",
        )
        assert plan.installment_count == 4
        assert plan.installments_paid == 0


# ──────────────────────────────────────────────────
# INSURANCE TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestInsurance:
    def test_insurance_card(self):
        from products.cymed.patient_portal.insurance.models import InsuranceCard

        card = InsuranceCard.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            insurer_name="National Health Insurance",
            policy_number="POL-2026-001",
            member_id="MEM-001",
            plan_name="Gold Plan",
            plan_type="individual",
            effective_date=date(2026, 1, 1),
            expiry_date=date(2026, 12, 31),
            is_primary=True,
            is_active=True,
            deductible=500.00,
            out_of_pocket_max=3000.00,
        )
        assert card.is_primary is True
        assert card.plan_type == "individual"

    def test_coverage_verification(self):
        from products.cymed.patient_portal.insurance.models import (
            CoverageVerification,
            InsuranceCard,
        )

        card = InsuranceCard.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            insurer_name="Health Insurer",
            policy_number="POL-2026-002",
            member_id="MEM-002",
        )
        verification = CoverageVerification.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            insurance_card=card,
            verification_type="specific_service",
            service_type="MRI Brain",
            status="verified",
            coverage_percentage=80,
            patient_responsibility=200.00,
        )
        assert verification.status == "verified"
        assert verification.coverage_percentage == 80

    def test_preauthorization_request(self):
        from products.cymed.patient_portal.insurance.models import (
            InsuranceCard,
            PreauthorizationRequest,
        )

        card = InsuranceCard.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            insurer_name="Test Insurer",
            policy_number="POL-003",
            member_id="MEM-003",
        )
        preauth = PreauthorizationRequest.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            insurance_card=card,
            service_type="Cardiac Catheterization",
            service_description="Diagnostic cardiac cath for suspected CAD.",
            provider_name="City Hospital",
            diagnosis_codes=["I25.10"],
            procedure_codes=["93460"],
            status="submitted",
        )
        assert preauth.status == "submitted"

    def test_claim_status(self):
        from products.cymed.patient_portal.insurance.models import ClaimStatus, InsuranceCard

        card = InsuranceCard.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            insurer_name="Test Insurer",
            policy_number="POL-004",
            member_id="MEM-004",
        )
        claim = ClaimStatus.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            insurance_card=card,
            claim_number="CLM-2026-001",
            service_date=date.today() - timedelta(days=30),
            service_type="Laboratory",
            provider_name="Alpha Lab",
            billed_amount=500.00,
            allowed_amount=400.00,
            paid_amount=320.00,
            patient_responsibility=80.00,
            status="paid",
        )
        assert claim.status == "paid"
        assert claim.paid_amount == 320.00


# ──────────────────────────────────────────────────
# DIGITAL WALLET TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestDigitalWallet:
    def test_health_wallet(self):
        from products.cymed.patient_portal.wallet.models import HealthWallet

        wallet = HealthWallet.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            wallet_name="My Health Wallet",
        )
        assert wallet.is_active is True
        assert wallet.card_count == 0

    def test_digital_card(self):
        from products.cymed.patient_portal.wallet.models import DigitalCard

        card = DigitalCard.objects.create(
            tenant_id=TENANT,
            wallet_account_id=ACCOUNT,
            card_type="insurance",
            card_title="National Health Insurance",
            card_number="POL-2026-001",
            issuer_name="NHI",
            holder_name="Ali Al-Nsour",
            valid_until=date(2026, 12, 31),
            is_active=True,
            display_order=1,
        )
        assert card.card_type == "insurance"
        assert card.holder_name == "Ali Al-Nsour"

    def test_health_pass(self):
        from products.cymed.patient_portal.wallet.models import HealthPass

        hp = HealthPass.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            pass_type="vaccination",
            title="COVID-19 Vaccination Certificate",
            issue_date=date(2024, 3, 1),
            issuer_name="Ministry of Health",
            status="valid",
            is_verified=True,
        )
        assert hp.pass_type == "vaccination"
        assert hp.status == "valid"
        assert hp.is_verified is True

    def test_vaccination_record(self):
        from products.cymed.patient_portal.wallet.models import VaccinationRecord

        vax = VaccinationRecord.objects.create(
            tenant_id=TENANT,
            account_id=ACCOUNT,
            patient_id=PATIENT,
            vaccine_name="COVID-19 Pfizer-BioNTech",
            manufacturer="Pfizer-BioNTech",
            lot_number="EJ1685",
            dose_number=2,
            total_doses_required=2,
            administered_date=date(2024, 4, 15),
            administered_by="Dr. Fatima Al-Zahra",
            facility_name="Ministry of Health Clinic",
            site="Left arm",
            route="IM",
            cvx_code="208",
        )
        assert vax.dose_number == 2
        assert vax.cvx_code == "208"
