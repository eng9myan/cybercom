import uuid

import pytest
from django.utils import timezone

from products.cymed.core.clinical.services import ClinicalAIService
from products.cymed.core.encounters.models import Encounter
from products.cymed.core.facilities.models import Facility
from products.cymed.core.organizations.models import Organization
from products.cymed.core.patients.models import Patient
from products.cymed.pharmacy.dispensing.models import DispenseOrder, DispenseStatus
from products.cymed.pharmacy.formulary.models import Formulary, FormularyDrug, TherapeuticClass
from products.cymed.pharmacy.prescriptions.models import (
    DEASchedule,
    Prescription,
    PrescriptionStatus,
    PrescriptionType,
)


@pytest.fixture
def test_tenant_id():
    return uuid.uuid4()


@pytest.fixture
def setup_pharmacy_base_data(test_tenant_id):
    org = Organization.objects.create(
        tenant_id=test_tenant_id, name="Hospital Org", slug="hosp-org", organization_type="hospital"
    )
    facility = Facility.objects.create(
        tenant_id=test_tenant_id, organization=org, name="Main Hospital Facility", code="MAIN-HOSP"
    )
    patient = Patient.objects.create(
        tenant_id=test_tenant_id,
        first_name="Ahmad",
        last_name="Kamal",
        dob="1985-05-15",
        mrn="MRN-PHARM-001",
    )
    encounter = Encounter.objects.create(
        tenant_id=test_tenant_id,
        patient=patient,
        encounter_type="inpatient",
        status="in_progress",
        organization=org,
        facility=facility,
    )

    return {
        "org": org,
        "facility": facility,
        "patient": patient,
        "encounter": encounter,
    }


@pytest.mark.django_db
class TestPharmacyEndToEndWorkflow:
    def test_full_prescription_to_dispensing_workflow(
        self, test_tenant_id, setup_pharmacy_base_data
    ):
        patient = setup_pharmacy_base_data["patient"]
        encounter = setup_pharmacy_base_data["encounter"]

        prescriber_id = uuid.uuid4()
        pharmacist_id = uuid.uuid4()

        # 1. Provider places medication order / prescription
        rx = Prescription.objects.create(
            tenant_id=test_tenant_id,
            prescription_number=f"RX-{uuid.uuid4().hex[:8].upper()}",
            patient_id=patient.id,
            encounter_id=encounter.id,
            prescriber_id=prescriber_id,
            prescription_type=PrescriptionType.OUTPATIENT,
            status=PrescriptionStatus.PENDING,
        )
        assert rx.id is not None

        # 2. Pharmacist receives and verifies order
        rx.status = PrescriptionStatus.ACTIVE
        rx.verified_by = pharmacist_id
        rx.verified_at = timezone.now()
        rx.save()

        # 3. Dispense Medication
        disp = DispenseOrder.objects.create(
            tenant_id=test_tenant_id,
            dispense_number=f"DSP-{uuid.uuid4().hex[:8].upper()}",
            prescription_id=rx.id,
            patient_id=patient.id,
            encounter_id=encounter.id,
            status=DispenseStatus.READY,
            pickup_method="counter",
        )
        assert disp.id is not None

        # 4. Patient pickup / counter dispense
        disp.status = DispenseStatus.DISPENSED
        disp.dispensed_by = pharmacist_id
        disp.dispensed_at = timezone.now()
        disp.picked_up_by = "Patient self"
        disp.pickup_id_verified = True
        disp.picked_up_at = timezone.now()
        disp.save()

        # Update prescription status
        rx.status = PrescriptionStatus.DISPENSED
        rx.dispensed_at = timezone.now()
        rx.save()

        # Verify final states
        assert rx.status == PrescriptionStatus.DISPENSED
        assert disp.status == DispenseStatus.DISPENSED

    def test_controlled_substance_workflow(self, test_tenant_id, setup_pharmacy_base_data):
        patient = setup_pharmacy_base_data["patient"]

        prescriber_id = uuid.uuid4()
        pharmacist_id = uuid.uuid4()

        # Controlled prescription (Schedule II)
        rx = Prescription.objects.create(
            tenant_id=test_tenant_id,
            prescription_number=f"RX-{uuid.uuid4().hex[:8].upper()}",
            patient_id=patient.id,
            prescriber_id=prescriber_id,
            prescription_type=PrescriptionType.CONTROLLED,
            status=PrescriptionStatus.PENDING,
            is_controlled=True,
            dea_schedule=DEASchedule.SCHEDULE_II,
            prescriber_dea="AB1234567",
        )
        assert rx.is_controlled is True

        # Dispense controlled substance with pharmacist verification
        disp = DispenseOrder.objects.create(
            tenant_id=test_tenant_id,
            dispense_number=f"DSP-{uuid.uuid4().hex[:8].upper()}",
            prescription_id=rx.id,
            patient_id=patient.id,
            status=DispenseStatus.VERIFICATION_PENDING,
            pickup_method="counter",
        )

        # Pharmacist double-checks and signs off
        disp.status = DispenseStatus.DISPENSED
        disp.verified_by = pharmacist_id
        disp.verified_at = timezone.now()
        disp.dispensed_by = pharmacist_id
        disp.dispensed_at = timezone.now()
        disp.picked_up_by = "Patient self"
        disp.pickup_id_verified = True
        disp.picked_up_at = timezone.now()
        disp.notes = "Double counted by R.Ph. Witness signature: Nurse Sarah"
        disp.save()

        assert disp.status == DispenseStatus.DISPENSED

    def test_drug_interaction_detection(self, test_tenant_id):
        # Call ClinicalAIService to test interaction checking logic
        patient_context = {"age_years": 76, "egfr": 25, "is_pregnant": False}
        res = ClinicalAIService.score_drug_interaction_severity(
            tenant_id=str(test_tenant_id),
            drug_a="warfarin",
            drug_b="aspirin",
            patient_context=patient_context,
        )
        assert res["severity"] == "major"
        assert res["confidence_score"] > 0.8
        assert len(res["context_modifiers"]) > 0

    def test_formulary_compliance(self, test_tenant_id):
        # Create a formulary
        form = Formulary.objects.create(
            tenant_id=test_tenant_id,
            name="Standard Hospital Formulary",
            is_default=True,
        )
        # Register a therapeutic class
        tc = TherapeuticClass.objects.create(
            tenant_id=test_tenant_id,
            code="ATC-C09AA",
            name="ACE inhibitors",
        )
        # Register formulary drug
        fd = FormularyDrug.objects.create(
            tenant_id=test_tenant_id,
            formulary=form,
            therapeutic_class=tc,
        )
        assert fd.id is not None
