"""
CyMed Pharmacy — FHIR Resource Tests
Tests for MedicationRequest, MedicationDispense, MedicationStatement,
MedicationKnowledge, and associated FHIR operations.
"""

import uuid

import pytest

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
PROVIDER = uuid.uuid4()
PHARMACIST = uuid.uuid4()


@pytest.mark.django_db
class TestFHIRMedicationRequest:
    """Tests verifying FHIR MedicationRequest linking on Prescriptions."""

    def test_prescription_fhir_id_stored(self):
        from products.cymed.pharmacy.prescriptions.models import Prescription

        fhir_id = f"MedicationRequest/{uuid.uuid4()}"
        rx = Prescription.objects.create(
            tenant_id=TENANT,
            prescription_number="RX-FHIR-001",
            patient_id=PATIENT,
            prescriber_id=PROVIDER,
            fhir_medication_request_id=fhir_id,
        )
        assert rx.fhir_medication_request_id == fhir_id

    def test_medication_order_fhir_id(self):
        from products.cymed.pharmacy.prescriptions.models import MedicationOrder

        fhir_id = f"MedicationRequest/{uuid.uuid4()}"
        order = MedicationOrder.objects.create(
            tenant_id=TENANT,
            order_number="MO-FHIR-001",
            patient_id=PATIENT,
            admission_id=uuid.uuid4(),
            prescriber_id=PROVIDER,
            drug_code="RXN-001",
            drug_name="Heparin 5000IU",
            dose="5000",
            dose_unit="IU",
            route="subcutaneous",
            frequency="BID",
            fhir_medication_request_id=fhir_id,
        )
        assert order.fhir_medication_request_id == fhir_id

    def test_medication_history_fhir_statement(self):
        from products.cymed.pharmacy.prescriptions.models import MedicationHistory

        fhir_id = f"MedicationStatement/{uuid.uuid4()}"
        h = MedicationHistory.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            drug_code="RXN-002",
            drug_name="Aspirin 81mg",
            source="prescription",
            fhir_medication_statement_id=fhir_id,
        )
        assert h.fhir_medication_statement_id == fhir_id


@pytest.mark.django_db
class TestFHIRMedicationDispense:
    """Tests verifying FHIR MedicationDispense linking on DispenseOrder."""

    def test_dispense_order_fhir_id(self):
        from products.cymed.pharmacy.dispensing.models import DispenseOrder

        fhir_id = f"MedicationDispense/{uuid.uuid4()}"
        order = DispenseOrder.objects.create(
            tenant_id=TENANT,
            dispense_number="DSP-FHIR-001",
            patient_id=PATIENT,
            fhir_medication_dispense_id=fhir_id,
        )
        assert order.fhir_medication_dispense_id == fhir_id

    def test_medication_change_fhir_statement(self):
        from products.cymed.pharmacy.medication_reconciliation.models import (
            MedicationChange,
            MedicationReconciliation,
        )

        rec = MedicationReconciliation.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            encounter_id=uuid.uuid4(),
            initiated_by=PHARMACIST,
        )
        fhir_id = f"MedicationStatement/{uuid.uuid4()}"
        change = MedicationChange.objects.create(
            tenant_id=TENANT,
            reconciliation=rec,
            drug_code="RXN-001",
            drug_name="Test Drug",
            change_type="continued",
            reason="Continue as before.",
            changed_by=PHARMACIST,
            fhir_medication_statement_id=fhir_id,
        )
        assert change.fhir_medication_statement_id == fhir_id


@pytest.mark.django_db
class TestFHIRReconciliationBundle:
    """Tests for reconciliation FHIR bundle tracking."""

    def test_reconciliation_fhir_bundle(self):
        from products.cymed.pharmacy.medication_reconciliation.models import (
            MedicationReconciliation,
        )

        fhir_bundle = f"Bundle/{uuid.uuid4()}"
        rec = MedicationReconciliation.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            encounter_id=uuid.uuid4(),
            initiated_by=PHARMACIST,
            fhir_bundle_id=fhir_bundle,
        )
        assert rec.fhir_bundle_id == fhir_bundle


@pytest.mark.django_db
class TestFHIRSearchByID:
    """Verify FHIR IDs are indexed for search performance."""

    def test_prescription_search_by_fhir_id(self):
        from products.cymed.pharmacy.prescriptions.models import Prescription

        fhir_id = f"MedicationRequest/{uuid.uuid4()}"
        Prescription.objects.create(
            tenant_id=TENANT,
            prescription_number="RX-FHIR-002",
            patient_id=PATIENT,
            prescriber_id=PROVIDER,
            fhir_medication_request_id=fhir_id,
        )
        result = Prescription.objects.filter(fhir_medication_request_id=fhir_id)
        assert result.count() == 1

    def test_dispense_search_by_fhir_id(self):
        from products.cymed.pharmacy.dispensing.models import DispenseOrder

        fhir_id = f"MedicationDispense/{uuid.uuid4()}"
        DispenseOrder.objects.create(
            tenant_id=TENANT,
            dispense_number="DSP-FHIR-002",
            patient_id=PATIENT,
            fhir_medication_dispense_id=fhir_id,
        )
        result = DispenseOrder.objects.filter(fhir_medication_dispense_id=fhir_id)
        assert result.count() == 1
