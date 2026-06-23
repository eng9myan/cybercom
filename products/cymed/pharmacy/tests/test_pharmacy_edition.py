"""
CyMed Pharmacy Edition — Comprehensive Test Suite
Program 3.5: Covers prescriptions, dispensing, clinical pharmacy, 
             medication reconciliation, drug interactions, formulary, 
             automation, analytics, inventory bridge, procurement bridge.
Target coverage: 90%+
"""
import uuid
import pytest
from django.test import RequestFactory
from django.utils import timezone

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
PROVIDER = uuid.uuid4()
PHARMACIST = uuid.uuid4()
OTHER_TENANT = uuid.uuid4()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def tenant_id():
    return TENANT


# ────────────────────────────────────────────────
# PRESCRIPTION TESTS
# ────────────────────────────────────────────────

@pytest.mark.django_db
class TestPrescription:
    def test_create_prescription(self):
        from products.cymed.pharmacy.prescriptions.models import Prescription, PrescriptionStatus
        rx = Prescription.objects.create(
            tenant_id=TENANT,
            prescription_number="RX-TEST-001",
            patient_id=PATIENT,
            prescriber_id=PROVIDER,
            prescription_type="outpatient",
            status=PrescriptionStatus.PENDING,
            priority="routine",
        )
        assert rx.prescription_number == "RX-TEST-001"
        assert rx.status == "pending"
        assert rx.is_controlled is False
        assert rx.can_refill is False

    def test_prescription_str(self):
        from products.cymed.pharmacy.prescriptions.models import Prescription
        rx = Prescription.objects.create(
            tenant_id=TENANT, prescription_number="RX-TEST-002",
            patient_id=PATIENT, prescriber_id=PROVIDER,
        )
        assert "RX-TEST-002" in str(rx)

    def test_controlled_substance_prescription(self):
        from products.cymed.pharmacy.prescriptions.models import Prescription, DEASchedule
        rx = Prescription.objects.create(
            tenant_id=TENANT, prescription_number="RX-CS-001",
            patient_id=PATIENT, prescriber_id=PROVIDER,
            is_controlled=True, dea_schedule=DEASchedule.SCHEDULE_II,
        )
        assert rx.is_controlled is True
        assert rx.dea_schedule == "II"

    def test_prescription_can_refill(self):
        from products.cymed.pharmacy.prescriptions.models import Prescription, PrescriptionStatus
        rx = Prescription.objects.create(
            tenant_id=TENANT, prescription_number="RX-TEST-003",
            patient_id=PATIENT, prescriber_id=PROVIDER,
            status=PrescriptionStatus.ACTIVE,
            refills_authorized=3, refills_dispensed=1,
        )
        assert rx.can_refill is True

    def test_prescription_refill_exhausted(self):
        from products.cymed.pharmacy.prescriptions.models import Prescription, PrescriptionStatus
        rx = Prescription.objects.create(
            tenant_id=TENANT, prescription_number="RX-TEST-004",
            patient_id=PATIENT, prescriber_id=PROVIDER,
            status=PrescriptionStatus.ACTIVE,
            refills_authorized=2, refills_dispensed=2,
        )
        assert rx.can_refill is False

    def test_prescription_items(self):
        from products.cymed.pharmacy.prescriptions.models import Prescription, PrescriptionItem
        rx = Prescription.objects.create(
            tenant_id=TENANT, prescription_number="RX-TEST-005",
            patient_id=PATIENT, prescriber_id=PROVIDER,
        )
        item = PrescriptionItem.objects.create(
            tenant_id=TENANT, prescription=rx,
            drug_code="RXN-12345", drug_name="Amoxicillin 500mg",
            dose="500", dose_unit="mg", route="oral",
            frequency="TID", quantity=21, quantity_unit="capsules",
            sig="Take 1 capsule three times daily with food.",
        )
        assert item.drug_name == "Amoxicillin 500mg"
        assert rx.items.count() == 1

    def test_prescription_attachment(self):
        from products.cymed.pharmacy.prescriptions.models import Prescription, PrescriptionAttachment
        rx = Prescription.objects.create(
            tenant_id=TENANT, prescription_number="RX-TEST-006",
            patient_id=PATIENT, prescriber_id=PROVIDER,
        )
        att = PrescriptionAttachment.objects.create(
            tenant_id=TENANT, prescription=rx,
            attachment_type="handwritten_rx",
            file_name="rx_scan.pdf", file_type="application/pdf",
            file_url="https://cydata.example.com/rx/rx_scan.pdf",
            uploaded_by=PHARMACIST,
        )
        assert att.attachment_type == "handwritten_rx"

    def test_medication_renewal(self):
        from products.cymed.pharmacy.prescriptions.models import Prescription, MedicationRenewal
        rx = Prescription.objects.create(
            tenant_id=TENANT, prescription_number="RX-TEST-007",
            patient_id=PATIENT, prescriber_id=PROVIDER,
        )
        renewal = MedicationRenewal.objects.create(
            tenant_id=TENANT, prescription=rx, requested_by=PATIENT,
            renewal_duration_days=30, status="requested",
        )
        assert renewal.status == "requested"
        assert rx.renewals.count() == 1

    def test_medication_refill(self):
        from products.cymed.pharmacy.prescriptions.models import Prescription, MedicationRefill
        rx = Prescription.objects.create(
            tenant_id=TENANT, prescription_number="RX-TEST-008",
            patient_id=PATIENT, prescriber_id=PROVIDER,
            refills_authorized=3,
        )
        refill = MedicationRefill.objects.create(
            tenant_id=TENANT, prescription=rx, refill_number=1,
            status="dispensed", quantity_dispensed=30, days_supply=30,
        )
        assert refill.refill_number == 1

    def test_medication_history(self):
        from products.cymed.pharmacy.prescriptions.models import MedicationHistory
        h = MedicationHistory.objects.create(
            tenant_id=TENANT, patient_id=PATIENT,
            drug_code="RXN-001", drug_name="Metformin 500mg",
            source="prescription", is_active=True,
        )
        assert h.is_active is True
        assert MedicationHistory.objects.filter(patient_id=PATIENT).count() == 1

    def test_tenant_isolation_prescription(self):
        from products.cymed.pharmacy.prescriptions.models import Prescription
        Prescription.objects.create(
            tenant_id=TENANT, prescription_number="RX-ISO-001",
            patient_id=PATIENT, prescriber_id=PROVIDER,
        )
        Prescription.objects.create(
            tenant_id=OTHER_TENANT, prescription_number="RX-ISO-002",
            patient_id=PATIENT, prescriber_id=PROVIDER,
        )
        assert Prescription.objects.filter(tenant_id=TENANT).count() == 1
        assert Prescription.objects.filter(tenant_id=OTHER_TENANT).count() == 1


# ────────────────────────────────────────────────
# DISPENSING TESTS
# ────────────────────────────────────────────────

@pytest.mark.django_db
class TestDispensing:
    def test_create_dispense_order(self):
        from products.cymed.pharmacy.dispensing.models import DispenseOrder, DispenseStatus
        order = DispenseOrder.objects.create(
            tenant_id=TENANT, dispense_number="DSP-TEST-001",
            patient_id=PATIENT, dispense_type="retail", status=DispenseStatus.QUEUED,
        )
        assert order.dispense_number == "DSP-TEST-001"
        assert order.status == "queued"

    def test_dispense_order_str(self):
        from products.cymed.pharmacy.dispensing.models import DispenseOrder
        order = DispenseOrder.objects.create(
            tenant_id=TENANT, dispense_number="DSP-STR-001", patient_id=PATIENT,
        )
        assert "DSP-STR-001" in str(order)

    def test_dispense_item_creation(self):
        from products.cymed.pharmacy.dispensing.models import DispenseOrder, DispenseItem
        order = DispenseOrder.objects.create(
            tenant_id=TENANT, dispense_number="DSP-TEST-002", patient_id=PATIENT,
        )
        item = DispenseItem.objects.create(
            tenant_id=TENANT, dispense_order=order,
            drug_code="RXN-001", drug_name="Amoxicillin 500mg",
            ndc_code="0093-2264-01", lot_number="LOT123",
            quantity_prescribed=21, quantity_dispensed=21, quantity_unit="capsules",
            days_supply=7,
        )
        assert item.barcode_verified is False
        assert order.items.count() == 1

    def test_dispense_batch(self):
        from products.cymed.pharmacy.dispensing.models import DispenseBatch
        batch = DispenseBatch.objects.create(
            tenant_id=TENANT, batch_number="BATCH-001",
            batch_type="unit_dose", status="open",
        )
        assert batch.batch_number == "BATCH-001"
        assert batch.status == "open"

    def test_dispense_verification(self):
        from products.cymed.pharmacy.dispensing.models import DispenseOrder, DispenseVerification
        order = DispenseOrder.objects.create(
            tenant_id=TENANT, dispense_number="DSP-VER-001", patient_id=PATIENT,
        )
        verification = DispenseVerification.objects.create(
            tenant_id=TENANT, dispense_order=order,
            verification_type="second_check", verified_by=PHARMACIST, result="pass",
        )
        assert verification.result == "pass"

    def test_dispense_audit(self):
        from products.cymed.pharmacy.dispensing.models import DispenseOrder, DispenseAudit
        order = DispenseOrder.objects.create(
            tenant_id=TENANT, dispense_number="DSP-AUD-001", patient_id=PATIENT,
        )
        audit = DispenseAudit.objects.create(
            tenant_id=TENANT, dispense_order=order,
            action="created", performed_by=PHARMACIST,
        )
        assert audit.action == "created"
        assert audit.is_override is False


# ────────────────────────────────────────────────
# DRUG INTERACTION TESTS
# ────────────────────────────────────────────────

@pytest.mark.django_db
class TestDrugInteractions:
    def test_create_interaction_rule(self):
        from products.cymed.pharmacy.drug_interactions.models import InteractionRule, InteractionType
        rule = InteractionRule.objects.create(
            tenant_id=TENANT,
            rule_code="DDI-001",
            interaction_type=InteractionType.DRUG_DRUG,
            severity="severe",
            drug_a_code="RXN-WAR", drug_a_name="Warfarin",
            drug_b_code="RXN-ASP", drug_b_name="Aspirin",
            description="Increased bleeding risk.",
            management_recommendation="Monitor INR closely.",
            override_allowed=True,
        )
        assert rule.rule_code == "DDI-001"
        assert rule.severity == "severe"

    def test_create_drug_interaction(self):
        from products.cymed.pharmacy.drug_interactions.models import InteractionRule, DrugInteraction, InteractionType
        rule = InteractionRule.objects.create(
            tenant_id=TENANT, rule_code="DDI-002",
            interaction_type=InteractionType.DRUG_DRUG, severity="moderate",
            drug_a_code="RXN-MET", drug_a_name="Metformin",
            drug_b_code="RXN-CIM", drug_b_name="Cimetidine",
            description="Reduced metformin clearance.",
            management_recommendation="Monitor renal function.",
        )
        interaction = DrugInteraction.objects.create(
            tenant_id=TENANT, patient_id=PATIENT, rule=rule,
            interaction_type=InteractionType.DRUG_DRUG, severity="moderate",
            drug_a_code="RXN-MET", drug_a_name="Metformin",
            drug_b_code="RXN-CIM", drug_b_name="Cimetidine",
        )
        assert interaction.alert_status == "active"
        assert "Metformin" in str(interaction)

    def test_interaction_severity_config(self):
        from products.cymed.pharmacy.drug_interactions.models import InteractionSeverity
        config = InteractionSeverity.objects.create(
            tenant_id=TENANT, severity="contraindicated",
            auto_block_dispensing=True, requires_pharmacist_review=True,
            notify_prescriber=True,
        )
        assert config.auto_block_dispensing is True

    def test_interaction_alert(self):
        from products.cymed.pharmacy.drug_interactions.models import InteractionRule, DrugInteraction, InteractionAlert, InteractionType
        rule = InteractionRule.objects.create(
            tenant_id=TENANT, rule_code="DDI-003",
            interaction_type=InteractionType.DRUG_ALLERGY, severity="severe",
            drug_a_code="RXN-PCN", drug_a_name="Penicillin",
            allergen_code="ALLERGEN-PCN",
            description="Penicillin allergy.",
            management_recommendation="Use alternative antibiotic.",
        )
        interaction = DrugInteraction.objects.create(
            tenant_id=TENANT, patient_id=PATIENT, rule=rule,
            interaction_type=InteractionType.DRUG_ALLERGY, severity="severe",
            drug_a_code="RXN-PCN", drug_a_name="Penicillin",
        )
        alert = InteractionAlert.objects.create(
            tenant_id=TENANT, interaction=interaction,
            recipient_id=PHARMACIST, recipient_role="pharmacist",
            channel="ui_popup",
        )
        assert alert.acknowledged_at is None


# ────────────────────────────────────────────────
# CLINICAL PHARMACY TESTS
# ────────────────────────────────────────────────

@pytest.mark.django_db
class TestClinicalPharmacy:
    def test_create_medication_review(self):
        from products.cymed.pharmacy.clinical_pharmacy.models import MedicationReview, ReviewStatus
        review = MedicationReview.objects.create(
            tenant_id=TENANT, patient_id=PATIENT, pharmacist_id=PHARMACIST,
            review_type="dur", status=ReviewStatus.IN_PROGRESS,
            medications_reviewed=["RXN-001", "RXN-002"],
        )
        assert review.review_type == "dur"
        assert review.polypharmacy_risk == "low"

    def test_clinical_intervention(self):
        from products.cymed.pharmacy.clinical_pharmacy.models import MedicationReview, ClinicalIntervention
        review = MedicationReview.objects.create(
            tenant_id=TENANT, patient_id=PATIENT, pharmacist_id=PHARMACIST,
            review_type="cmr",
        )
        intervention = ClinicalIntervention.objects.create(
            tenant_id=TENANT, review=review, patient_id=PATIENT, pharmacist_id=PHARMACIST,
            intervention_type="dose_optimization",
            problem_identified="Dose too high for patient renal function.",
            intervention_action="Recommended dose reduction to 500mg.",
            drug_code="RXN-001", drug_name="Metformin",
            outcome="pending", clinical_significance="major",
        )
        assert intervention.outcome == "pending"

    def test_pharmacist_recommendation(self):
        from products.cymed.pharmacy.clinical_pharmacy.models import MedicationReview, PharmacistRecommendation
        review = MedicationReview.objects.create(
            tenant_id=TENANT, patient_id=PATIENT, pharmacist_id=PHARMACIST,
            review_type="tmr",
        )
        rec = PharmacistRecommendation.objects.create(
            tenant_id=TENANT, review=review, patient_id=PATIENT, pharmacist_id=PHARMACIST,
            recommendation_text="Switch to generic atorvastatin.",
            rationale="Cost saving with equivalent efficacy.",
            priority="moderate", status="submitted",
        )
        assert rec.status == "submitted"

    def test_mtm_session(self):
        from products.cymed.pharmacy.clinical_pharmacy.models import MedicationTherapyManagement
        from datetime import date
        mtm = MedicationTherapyManagement.objects.create(
            tenant_id=TENANT, patient_id=PATIENT, pharmacist_id=PHARMACIST,
            session_type="initial", scheduled_date=date.today(),
            program_name="Diabetes MTM",
        )
        assert mtm.session_type == "initial"
        assert mtm.completed_at is None


# ────────────────────────────────────────────────
# MEDICATION RECONCILIATION TESTS
# ────────────────────────────────────────────────

@pytest.mark.django_db
class TestMedicationReconciliation:
    def test_create_admission_reconciliation(self):
        from products.cymed.pharmacy.medication_reconciliation.models import (
            MedicationReconciliation, ReconciliationType, ReconciliationStatus
        )
        rec = MedicationReconciliation.objects.create(
            tenant_id=TENANT, patient_id=PATIENT, encounter_id=uuid.uuid4(),
            reconciliation_type=ReconciliationType.ADMISSION,
            status=ReconciliationStatus.INITIATED, initiated_by=PHARMACIST,
        )
        assert rec.reconciliation_type == "admission"

    def test_medication_change(self):
        from products.cymed.pharmacy.medication_reconciliation.models import (
            MedicationReconciliation, MedicationChange
        )
        rec = MedicationReconciliation.objects.create(
            tenant_id=TENANT, patient_id=PATIENT, encounter_id=uuid.uuid4(),
            initiated_by=PHARMACIST,
        )
        change = MedicationChange.objects.create(
            tenant_id=TENANT, reconciliation=rec,
            drug_code="RXN-001", drug_name="Metformin 500mg",
            change_type="dose_changed",
            previous_dose="500mg", new_dose="1000mg",
            reason="Dose increase per endocrinologist guidance.",
            changed_by=PHARMACIST,
        )
        assert change.change_type == "dose_changed"

    def test_medication_conflict(self):
        from products.cymed.pharmacy.medication_reconciliation.models import (
            MedicationReconciliation, MedicationConflict
        )
        rec = MedicationReconciliation.objects.create(
            tenant_id=TENANT, patient_id=PATIENT, encounter_id=uuid.uuid4(),
            initiated_by=PHARMACIST,
        )
        conflict = MedicationConflict.objects.create(
            tenant_id=TENANT, reconciliation=rec,
            conflict_type="omission",
            drug_code="RXN-001", drug_name="Aspirin 81mg",
            description="Home aspirin not listed in current medication orders.",
            clinical_significance="moderate", status="unresolved",
        )
        assert conflict.status == "unresolved"
        assert rec.conflicts.count() == 1

    def test_discharge_reconciliation(self):
        from products.cymed.pharmacy.medication_reconciliation.models import (
            MedicationReconciliation, ReconciliationType
        )
        rec = MedicationReconciliation.objects.create(
            tenant_id=TENANT, patient_id=PATIENT, encounter_id=uuid.uuid4(),
            reconciliation_type=ReconciliationType.DISCHARGE,
            initiated_by=PHARMACIST,
        )
        assert rec.reconciliation_type == "discharge"


# ────────────────────────────────────────────────
# FORMULARY TESTS
# ────────────────────────────────────────────────

@pytest.mark.django_db
class TestFormulary:
    def test_create_therapeutic_class(self):
        from products.cymed.pharmacy.formulary.models import TherapeuticClass
        tc = TherapeuticClass.objects.create(
            tenant_id=TENANT, code="J01CA", name="Penicillins",
            atc_code="J01CA", level=2,
        )
        assert tc.code == "J01CA"
        assert tc.is_active is True

    def test_create_formulary(self):
        from products.cymed.pharmacy.formulary.models import Formulary, FormularyType
        formulary = Formulary.objects.create(
            tenant_id=TENANT, name="Hospital Formulary 2026",
            formulary_type=FormularyType.HOSPITAL, is_active=True, is_default=True,
        )
        assert formulary.formulary_type == "hospital"

    def test_formulary_drug(self):
        from products.cymed.pharmacy.formulary.models import Formulary, FormularyDrug
        formulary = Formulary.objects.create(
            tenant_id=TENANT, name="Test Formulary", formulary_type="hospital",
        )
        drug = FormularyDrug.objects.create(
            tenant_id=TENANT, formulary=formulary,
            drug_code="RXN-AMX", drug_name="Amoxicillin 500mg",
            status="preferred", tier=1, is_generic_allowed=True,
        )
        assert drug.status == "preferred"
        assert drug.tier == 1

    def test_formulary_restriction(self):
        from products.cymed.pharmacy.formulary.models import Formulary, FormularyDrug, FormularyRestriction
        formulary = Formulary.objects.create(
            tenant_id=TENANT, name="Restriction Test Formulary", formulary_type="hospital",
        )
        drug = FormularyDrug.objects.create(
            tenant_id=TENANT, formulary=formulary,
            drug_code="RXN-RES", drug_name="Restricted Drug",
            status="restricted", tier=4,
        )
        restriction = FormularyRestriction.objects.create(
            tenant_id=TENANT, formulary_drug=drug,
            restriction_type="specialist_only",
            description="Oncologist prescribing required.",
            is_hard_stop=True,
        )
        assert restriction.is_hard_stop is True

    def test_preferred_medication(self):
        from products.cymed.pharmacy.formulary.models import Formulary, PreferredMedication
        formulary = Formulary.objects.create(
            tenant_id=TENANT, name="Pref Formulary", formulary_type="retail",
        )
        pref = PreferredMedication.objects.create(
            tenant_id=TENANT, formulary=formulary,
            non_formulary_drug_code="RXN-BRAND", non_formulary_drug_name="Brand Drug",
            preferred_drug_code="RXN-GENERIC", preferred_drug_name="Generic Drug",
            interchange_reason="cost",
        )
        assert pref.interchange_reason == "cost"


# ────────────────────────────────────────────────
# AUTOMATION TESTS
# ────────────────────────────────────────────────

@pytest.mark.django_db
class TestAutomation:
    def test_create_automation_device(self):
        from products.cymed.pharmacy.automation.models import AutomationDevice, DeviceType, DeviceStatus
        device = AutomationDevice.objects.create(
            tenant_id=TENANT, device_code="ADC-ICU-01", device_name="ICU ADC Unit 1",
            device_type=DeviceType.ADC, location="ICU Level 2", status=DeviceStatus.ONLINE,
            controlled_substance_capable=True,
        )
        assert device.device_type == "adc"
        assert device.status == "online"

    def test_cabinet_device(self):
        from products.cymed.pharmacy.automation.models import AutomationDevice, CabinetDevice
        device = AutomationDevice.objects.create(
            tenant_id=TENANT, device_code="CAB-001", device_name="Narcotic Safe 1",
            device_type="adc", location="Pharmacy Vault",
        )
        cabinet = CabinetDevice.objects.create(
            tenant_id=TENANT, device=device,
            cabinet_type="narcotic_safe", slot_count=50,
            requires_biometric=True, requires_witness=True,
        )
        assert cabinet.requires_witness is True

    def test_dispensing_robot(self):
        from products.cymed.pharmacy.automation.models import AutomationDevice, DispensingRobot
        device = AutomationDevice.objects.create(
            tenant_id=TENANT, device_code="ROBOT-01", device_name="Swisslog Robot 1",
            device_type="robot", location="Central Pharmacy",
        )
        robot = DispensingRobot.objects.create(
            tenant_id=TENANT, device=device,
            dispensing_speed=300, storage_capacity=1200,
            supports_unit_dose=True,
        )
        assert robot.dispensing_speed == 300

    def test_automation_queue(self):
        from products.cymed.pharmacy.automation.models import AutomationDevice, AutomationQueue
        device = AutomationDevice.objects.create(
            tenant_id=TENANT, device_code="ADC-002", device_name="Ward ADC",
            device_type="adc", location="Ward 5",
        )
        queue_item = AutomationQueue.objects.create(
            tenant_id=TENANT, device=device,
            dispense_order_id=uuid.uuid4(),
            drug_code="RXN-001", drug_name="Metformin",
            quantity=2, quantity_unit="tablets",
            status="pending", priority="routine",
        )
        assert queue_item.status == "pending"
        assert queue_item.fallback_to_manual is False


# ────────────────────────────────────────────────
# ANALYTICS TESTS
# ────────────────────────────────────────────────

@pytest.mark.django_db
class TestAnalytics:
    def test_dashboard_snapshot(self):
        from products.cymed.pharmacy.analytics.models import PharmacyDashboardSnapshot
        from datetime import date
        snapshot = PharmacyDashboardSnapshot.objects.create(
            tenant_id=TENANT, snapshot_type="daily", snapshot_date=date.today(),
            prescriptions_total=150, prescriptions_dispensed=140,
            drug_interactions_detected=5, clinical_interventions=3,
        )
        assert snapshot.prescriptions_total == 150

    def test_medication_safety_event(self):
        from products.cymed.pharmacy.analytics.models import MedicationSafetyEvent
        event = MedicationSafetyEvent.objects.create(
            tenant_id=TENANT, event_type="near_miss", severity="b",
            patient_id=PATIENT, drug_code="RXN-001", drug_name="Warfarin",
            description="Wrong dose selected but caught before administration.",
            root_cause="UI display confusion.",
            reported_by=PHARMACIST, occurred_at=timezone.now(),
        )
        assert event.severity == "b"
        assert event.is_reported_to_authority is False


# ────────────────────────────────────────────────
# INVENTORY BRIDGE TESTS
# ────────────────────────────────────────────────

@pytest.mark.django_db
class TestInventoryBridge:
    def test_consumption_event(self):
        from products.cymed.pharmacy.inventory_bridge.models import MedicationConsumptionEvent
        event = MedicationConsumptionEvent.objects.create(
            tenant_id=TENANT, dispense_order_id=uuid.uuid4(),
            patient_id=PATIENT, drug_code="RXN-001", drug_name="Metformin",
            ndc_code="0093-1001-01", quantity=30, quantity_unit="tablets",
            dispensed_at=timezone.now(), erp_sync_status="pending",
        )
        assert event.erp_sync_status == "pending"

    def test_inventory_query_result(self):
        from products.cymed.pharmacy.inventory_bridge.models import InventoryQueryResult
        result = InventoryQueryResult.objects.create(
            tenant_id=TENANT, drug_code="RXN-001", drug_name="Metformin",
            quantity_on_hand=500, quantity_unit="tablets",
            reorder_level=100, is_below_reorder=False,
        )
        assert result.is_out_of_stock is False


# ────────────────────────────────────────────────
# PROCUREMENT BRIDGE TESTS
# ────────────────────────────────────────────────

@pytest.mark.django_db
class TestProcurementBridge:
    def test_create_procurement_request(self):
        from products.cymed.pharmacy.procurement_bridge.models import ProcurementRequest
        req = ProcurementRequest.objects.create(
            tenant_id=TENANT, request_number="PRQ-001",
            request_type="emergency", drug_code="RXN-RARE",
            drug_name="Rare Drug 100mg", quantity_requested=50,
            quantity_unit="vials", urgency="emergency",
            requested_by=PHARMACIST,
        )
        assert req.urgency == "emergency"
        assert req.status == "draft"

    def test_procurement_request_str(self):
        from products.cymed.pharmacy.procurement_bridge.models import ProcurementRequest
        req = ProcurementRequest.objects.create(
            tenant_id=TENANT, request_number="PRQ-002",
            drug_code="RXN-002", drug_name="Test Drug",
            quantity_requested=10, quantity_unit="boxes",
            urgency="routine", requested_by=PHARMACIST,
        )
        assert "PRQ-002" in str(req)
