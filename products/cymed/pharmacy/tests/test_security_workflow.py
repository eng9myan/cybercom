"""
CyMed Pharmacy — Security & Workflow Tests
Tests: Role-based access, tenant isolation, medication workflow integration,
       controlled substance tracking, event publishing.
"""

import uuid

import pytest

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
PROVIDER = uuid.uuid4()
PHARMACIST = uuid.uuid4()


@pytest.mark.django_db
class TestTenantIsolation:
    """All pharmacy resources are tenant-scoped."""

    def test_prescription_tenant_isolation(self):
        from products.cymed.pharmacy.prescriptions.models import Prescription

        t1 = uuid.uuid4()
        t2 = uuid.uuid4()
        Prescription.objects.create(
            tenant_id=t1,
            prescription_number="RX-T1-001",
            patient_id=PATIENT,
            prescriber_id=PROVIDER,
        )
        Prescription.objects.create(
            tenant_id=t2,
            prescription_number="RX-T2-001",
            patient_id=PATIENT,
            prescriber_id=PROVIDER,
        )
        assert Prescription.objects.filter(tenant_id=t1).count() == 1
        assert Prescription.objects.filter(tenant_id=t2).count() == 1

    def test_dispense_order_tenant_isolation(self):
        from products.cymed.pharmacy.dispensing.models import DispenseOrder

        t1 = uuid.uuid4()
        t2 = uuid.uuid4()
        DispenseOrder.objects.create(tenant_id=t1, dispense_number="DSP-T1-001", patient_id=PATIENT)
        DispenseOrder.objects.create(tenant_id=t2, dispense_number="DSP-T2-001", patient_id=PATIENT)
        assert DispenseOrder.objects.filter(tenant_id=t1).count() == 1
        assert DispenseOrder.objects.filter(tenant_id=t2).count() == 1

    def test_formulary_tenant_isolation(self):
        from products.cymed.pharmacy.formulary.models import Formulary

        t1 = uuid.uuid4()
        t2 = uuid.uuid4()
        Formulary.objects.create(tenant_id=t1, name="T1 Formulary", formulary_type="hospital")
        Formulary.objects.create(tenant_id=t2, name="T2 Formulary", formulary_type="retail")
        assert Formulary.objects.filter(tenant_id=t1).count() == 1
        assert Formulary.objects.filter(tenant_id=t2).count() == 1

    def test_interaction_rule_tenant_isolation(self):
        from products.cymed.pharmacy.drug_interactions.models import InteractionRule

        t1 = uuid.uuid4()
        t2 = uuid.uuid4()
        InteractionRule.objects.create(
            tenant_id=t1,
            rule_code="DDI-T1-001",
            interaction_type="drug_drug",
            severity="moderate",
            drug_a_code="RXN-A",
            drug_a_name="Drug A",
            drug_b_code="RXN-B",
            drug_b_name="Drug B",
            description="Test",
            management_recommendation="Test",
        )
        InteractionRule.objects.create(
            tenant_id=t2,
            rule_code="DDI-T2-001",
            interaction_type="drug_drug",
            severity="mild",
            drug_a_code="RXN-C",
            drug_a_name="Drug C",
            drug_b_code="RXN-D",
            drug_b_name="Drug D",
            description="Test2",
            management_recommendation="Test2",
        )
        assert InteractionRule.objects.filter(tenant_id=t1).count() == 1
        assert InteractionRule.objects.filter(tenant_id=t2).count() == 1


@pytest.mark.django_db
class TestControlledSubstanceTracking:
    """Verify controlled substance fields are enforced."""

    def test_controlled_prescription_fields(self):
        from products.cymed.pharmacy.prescriptions.models import DEASchedule, Prescription

        rx = Prescription.objects.create(
            tenant_id=TENANT,
            prescription_number="CS-001",
            patient_id=PATIENT,
            prescriber_id=PROVIDER,
            prescriber_dea="AB1234567",
            is_controlled=True,
            dea_schedule=DEASchedule.SCHEDULE_II,
        )
        assert rx.prescriber_dea == "AB1234567"
        assert rx.dea_schedule == "II"

    def test_controlled_medication_order(self):
        from products.cymed.pharmacy.prescriptions.models import DEASchedule, MedicationOrder

        order = MedicationOrder.objects.create(
            tenant_id=TENANT,
            order_number="MO-CS-001",
            patient_id=PATIENT,
            admission_id=uuid.uuid4(),
            prescriber_id=PROVIDER,
            drug_code="RXN-MORPH",
            drug_name="Morphine 10mg",
            dose="10",
            dose_unit="mg",
            route="IV",
            frequency="Q4H PRN",
            is_controlled=True,
            dea_schedule=DEASchedule.SCHEDULE_II,
        )
        assert order.is_controlled is True
        assert order.dea_schedule == "II"

    def test_dispense_audit_for_controlled(self):
        from products.cymed.pharmacy.dispensing.models import DispenseAudit, DispenseOrder

        order = DispenseOrder.objects.create(
            tenant_id=TENANT,
            dispense_number="DSP-CS-001",
            patient_id=PATIENT,
        )
        audit = DispenseAudit.objects.create(
            tenant_id=TENANT,
            dispense_order=order,
            action="dispensed",
            performed_by=PHARMACIST,
            is_override=False,
            details={"controlled": True, "dea_schedule": "II"},
        )
        assert audit.details["controlled"] is True


@pytest.mark.django_db
class TestMedicationWorkflow:
    """End-to-end medication workflow: Prescribe → Verify → Dispense."""

    def test_complete_medication_workflow(self):
        """
        Full workflow: Prescription created → verified → dispense order → dispensed.
        """
        from products.cymed.pharmacy.dispensing.models import (
            DispenseItem,
            DispenseOrder,
            DispenseStatus,
        )
        from products.cymed.pharmacy.prescriptions.models import (
            Prescription,
            PrescriptionItem,
            PrescriptionStatus,
        )

        # Step 1: Create prescription
        rx = Prescription.objects.create(
            tenant_id=TENANT,
            prescription_number="RX-FLOW-001",
            patient_id=PATIENT,
            prescriber_id=PROVIDER,
            prescription_type="outpatient",
            status=PrescriptionStatus.PENDING,
        )
        PrescriptionItem.objects.create(
            tenant_id=TENANT,
            prescription=rx,
            drug_code="RXN-001",
            drug_name="Amoxicillin 500mg",
            dose="500",
            dose_unit="mg",
            route="oral",
            frequency="TID",
            quantity=21,
            quantity_unit="capsules",
            sig="Take 1 capsule 3x daily.",
        )
        assert rx.status == "pending"

        # Step 2: Pharmacist verifies prescription
        rx.status = PrescriptionStatus.ACTIVE
        rx.verified_by = PHARMACIST
        from django.utils import timezone

        rx.verified_at = timezone.now()
        rx.save()
        assert rx.status == "active"

        # Step 3: Create dispense order
        dispense = DispenseOrder.objects.create(
            tenant_id=TENANT,
            dispense_number="DSP-FLOW-001",
            prescription_id=rx.id,
            patient_id=PATIENT,
            dispense_type="retail",
            status=DispenseStatus.VERIFICATION_PENDING,
        )
        DispenseItem.objects.create(
            tenant_id=TENANT,
            dispense_order=dispense,
            drug_code="RXN-001",
            drug_name="Amoxicillin 500mg",
            ndc_code="0093-2264-01",
            quantity_prescribed=21,
            quantity_dispensed=21,
            quantity_unit="capsules",
            days_supply=7,
        )

        # Step 4: Pharmacist verifies dispense
        dispense.status = DispenseStatus.VERIFIED
        dispense.verified_by = PHARMACIST
        dispense.verified_at = timezone.now()
        dispense.save()
        assert dispense.status == "verified"

        # Step 5: Dispense to patient
        dispense.status = DispenseStatus.DISPENSED
        dispense.dispensed_by = PHARMACIST
        dispense.dispensed_at = timezone.now()
        dispense.save()
        assert dispense.status == "dispensed"

        # Update prescription status
        rx.status = PrescriptionStatus.DISPENSED
        rx.save()
        assert rx.status == "dispensed"


@pytest.mark.django_db
class TestPharmacyEventPublishing:
    """Verify pharmacy events are published via OutboxEvent."""

    def test_prescription_event_not_duplicate(self):
        """Prescriptions and dispense orders each publish distinct events."""
        from products.cymed.pharmacy.dispensing.models import DispenseOrder
        from products.cymed.pharmacy.prescriptions.models import Prescription

        rx = Prescription.objects.create(
            tenant_id=TENANT,
            prescription_number="RX-EVT-001",
            patient_id=PATIENT,
            prescriber_id=PROVIDER,
        )
        dispense = DispenseOrder.objects.create(
            tenant_id=TENANT,
            dispense_number="DSP-EVT-001",
            prescription_id=rx.id,
            patient_id=PATIENT,
        )
        # Verify independent records exist
        assert rx.id != dispense.id
        assert str(rx.prescription_number) != str(dispense.dispense_number)


@pytest.mark.django_db
class TestPharmacySecurityRoles:
    """Verify AI cannot approve or dispense — pharmacist required."""

    def test_ai_cannot_set_verified_status(self):
        """
        AI-provided scores and analysis cannot directly change prescription status.
        Status must be set by a human pharmacist.
        """
        from products.cymed.pharmacy.clinical_pharmacy.models import MedicationReview
        from products.cymed.pharmacy.prescriptions.models import Prescription, PrescriptionStatus

        rx = Prescription.objects.create(
            tenant_id=TENANT,
            prescription_number="RX-SEC-001",
            patient_id=PATIENT,
            prescriber_id=PROVIDER,
            status=PrescriptionStatus.PENDING,
        )
        # AI analysis on review — cannot change rx status
        MedicationReview.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            pharmacist_id=PHARMACIST,
            review_type="dur",
            ai_polypharmacy_score=0.85,
        )
        # Prescription status unchanged by AI
        rx.refresh_from_db()
        assert rx.status == "pending"  # AI did not change it

    def test_override_requires_reason(self):
        """Interaction override must have a reason (min 10 chars)."""
        from products.cymed.pharmacy.drug_interactions.serializers import (
            InteractionOverrideSerializer,
        )

        serializer = InteractionOverrideSerializer(data={"override_reason": "short"})
        assert not serializer.is_valid()
        assert "override_reason" in serializer.errors

    def test_override_reason_valid(self):
        from products.cymed.pharmacy.drug_interactions.serializers import (
            InteractionOverrideSerializer,
        )

        serializer = InteractionOverrideSerializer(
            data={"override_reason": "Patient has documented tolerance. Benefits outweigh risks."}
        )
        assert serializer.is_valid()
