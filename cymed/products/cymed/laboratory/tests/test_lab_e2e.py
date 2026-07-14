import uuid

import pytest
from django.utils import timezone

from products.cymed.core.clinical.services import ClinicalAIService
from products.cymed.core.encounters.models import Encounter
from products.cymed.core.facilities.models import Facility
from products.cymed.core.organizations.models import Organization
from products.cymed.core.patients.models import Patient
from products.cymed.laboratory.orders.models import LabOrder, LabTest, LabTestCategory
from products.cymed.laboratory.reference_lab.models import ReferenceLab, ReferenceLabOrder
from products.cymed.laboratory.results.models import (
    InterpretationCode,
    LabResult,
    ResultStatus,
    ResultValue,
)
from products.cymed.laboratory.specimens.models import Specimen, SpecimenStatus
from products.cymed.laboratory.worklists.models import LabWorklist, WorklistItem


@pytest.fixture
def test_tenant_id():
    return uuid.uuid4()


@pytest.fixture
def setup_lab_base_data(test_tenant_id):
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
        mrn="MRN-LAB-001",
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
class TestLabEndToEndWorkflow:
    def test_full_lab_order_to_result_workflow(self, test_tenant_id, setup_lab_base_data):
        patient = setup_lab_base_data["patient"]
        encounter = setup_lab_base_data["encounter"]

        provider_id = uuid.uuid4()
        tech_id = uuid.uuid4()

        # 1. Clinician orders a test (CMP)
        test_cmp = LabTest.objects.create(
            tenant_id=test_tenant_id,
            code="CMP",
            name="Comprehensive Metabolic Panel",
            loinc_code="80053",
            category=LabTestCategory.CHEMISTRY,
        )

        order = LabOrder.objects.create(
            tenant_id=test_tenant_id,
            order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            patient_id=patient.id,
            encounter_id=encounter.id,
            ordered_by=provider_id,
            order_type="hospital",
            status="submitted",
        )

        from products.cymed.laboratory.orders.models import LabOrderItem

        item = LabOrderItem.objects.create(
            tenant_id=test_tenant_id,
            order=order,
            test=test_cmp,
            status="submitted",
        )

        # 2. Specimen collection with chain of custody
        spec = Specimen.objects.create(
            tenant_id=test_tenant_id,
            specimen_number=f"SPC-{uuid.uuid4().hex[:8].upper()}",
            barcode=f"BAR-{uuid.uuid4().hex[:6].upper()}",
            order_item=item,
            patient_id=patient.id,
            specimen_type="serum",
            status=SpecimenStatus.COLLECTED,
            collected_at=timezone.now(),
        )

        from products.cymed.laboratory.specimens.models import SpecimenCollection

        SpecimenCollection.objects.create(
            tenant_id=test_tenant_id,
            specimen=spec,
            collected_by=provider_id,
            collected_at=timezone.now(),
            collection_site="phlebotomy_room",
        )

        # 3. Specimen reception and accession
        spec.status = SpecimenStatus.RECEIVED
        spec.received_at = timezone.now()
        spec.save()

        # 4. Worklist assignment
        wl = LabWorklist.objects.create(
            tenant_id=test_tenant_id,
            name="Daily Chem Queue",
            department="chemistry",
            worklist_date=timezone.now().date(),
            status="in_progress",
            created_by=tech_id,
        )

        WorklistItem.objects.create(
            tenant_id=test_tenant_id,
            worklist=wl,
            order_item=item,
            status="in_progress",
        )

        # 5. Result entry
        res = LabResult.objects.create(
            tenant_id=test_tenant_id,
            order_item=item,
            specimen=spec,
            status=ResultStatus.RESULTED,
            resulted_by=tech_id,
            resulted_at=timezone.now(),
        )

        val_potassium = ResultValue.objects.create(
            tenant_id=test_tenant_id,
            result=res,
            analyte_code="K",
            analyte_name="Potassium",
            loinc_code="6298-4",
            value_type="numeric",
            value_numeric=6.2,  # critical high
            unit="mmol/L",
            interpretation=InterpretationCode.HIGH_HIGH,
            is_critical=True,
        )

        # 6. Critical value alert triggered
        if val_potassium.is_critical:
            res.has_critical_value = True
            res.save()

            # AI evaluation
            ai_res = ClinicalAIService.assess_critical_lab_value(
                tenant_id=str(test_tenant_id),
                patient_id=str(patient.id),
                loinc_code=val_potassium.loinc_code,
                result_value=float(val_potassium.value_numeric),
                unit=val_potassium.unit,
                normal_range_low=3.5,
                normal_range_high=5.1,
                critical_range_low=2.8,
                critical_range_high=6.0,
            )
            assert ai_res["is_critical"] is True
            assert ai_res["urgency"] == "critical"

        # 7. Result verification and sign-out
        res.status = ResultStatus.APPROVED
        res.approved_by = tech_id
        res.approved_at = timezone.now()
        res.save()

        # Update order item and order status
        item.status = "completed"
        item.save()
        order.status = "completed"
        order.save()

        assert res.status == ResultStatus.APPROVED
        assert order.status == "completed"

    def test_critical_value_notification(self, test_tenant_id, setup_lab_base_data):
        patient = setup_lab_base_data["patient"]
        # Fast test for potassium critical alert check
        ai_res = ClinicalAIService.assess_critical_lab_value(
            tenant_id=str(test_tenant_id),
            patient_id=str(patient.id),
            loinc_code="6298-4",
            result_value=6.5,
            unit="mmol/L",
            normal_range_low=3.5,
            normal_range_high=5.1,
            critical_range_low=2.8,
            critical_range_high=6.0,
        )
        assert ai_res["is_critical"] is True

    def test_specimen_rejection(self, test_tenant_id, setup_lab_base_data):
        patient = setup_lab_base_data["patient"]
        encounter = setup_lab_base_data["encounter"]

        test_cmp = LabTest.objects.create(
            tenant_id=test_tenant_id,
            code="CMP-2",
            name="Metabolic Panel 2",
            loinc_code="80053",
        )
        order = LabOrder.objects.create(
            tenant_id=test_tenant_id,
            order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            patient_id=patient.id,
            encounter_id=encounter.id,
            ordered_by=uuid.uuid4(),
            order_type="clinic",
            status="submitted",
        )
        from products.cymed.laboratory.orders.models import LabOrderItem

        item = LabOrderItem.objects.create(
            tenant_id=test_tenant_id,
            order=order,
            test=test_cmp,
            status="submitted",
        )

        spec = Specimen.objects.create(
            tenant_id=test_tenant_id,
            specimen_number=f"SPC-{uuid.uuid4().hex[:8].upper()}",
            order_item=item,
            patient_id=patient.id,
            specimen_type="blood",
            status=SpecimenStatus.REJECTED,
        )

        from products.cymed.laboratory.specimens.models import SpecimenRejection

        rej = SpecimenRejection.objects.create(
            tenant_id=test_tenant_id,
            specimen=spec,
            rejection_reason="hemolyzed",
            rejected_by=uuid.uuid4(),
            rejected_at=timezone.now(),
        )
        assert rej.id is not None
        assert spec.status == SpecimenStatus.REJECTED

    def test_reference_lab_routing(self, test_tenant_id, setup_lab_base_data):
        patient = setup_lab_base_data["patient"]
        encounter = setup_lab_base_data["encounter"]

        test_cmp = LabTest.objects.create(
            tenant_id=test_tenant_id,
            code="CMP-3",
            name="Metabolic Panel 3",
            loinc_code="80053",
        )
        order = LabOrder.objects.create(
            tenant_id=test_tenant_id,
            order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            patient_id=patient.id,
            encounter_id=encounter.id,
            ordered_by=uuid.uuid4(),
            order_type="clinic",
            status="submitted",
        )
        from products.cymed.laboratory.orders.models import LabOrderItem

        item = LabOrderItem.objects.create(
            tenant_id=test_tenant_id,
            order=order,
            test=test_cmp,
            status="submitted",
        )

        ref_lab = ReferenceLab.objects.create(
            tenant_id=test_tenant_id,
            code="MAYO",
            name="Mayo Clinic Laboratories",
            integration_type="fhir",
        )

        # Create reference lab order routing
        ref_ord = ReferenceLabOrder.objects.create(
            tenant_id=test_tenant_id,
            local_order_item=item,
            reference_lab=ref_lab,
            status="sent",
            sent_at=timezone.now(),
        )
        assert ref_ord.id is not None
