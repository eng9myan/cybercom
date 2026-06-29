"""
CyMed Provider Portal — Clinical, Orders, Results, Care Team, Approvals Tests (Phase 3.7)
"""

import uuid
from datetime import date, time, timedelta

import pytest
from django.utils import timezone

TENANT = uuid.uuid4()
PROVIDER = uuid.uuid4()
PROVIDER_2 = uuid.uuid4()
PATIENT = uuid.uuid4()
OTHER_TENANT = uuid.uuid4()
UNIT_ID = uuid.uuid4()


# ──────────────────────────────────────────────────
# CLINICAL DOCUMENTATION TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestClinicalDocumentation:
    def test_create_documentation_template(self):
        from products.cymed.provider_portal.clinical_documentation.models import (
            DocumentationTemplate,
        )

        template = DocumentationTemplate.objects.create(
            tenant_id=TENANT,
            name="Cardiology SOAP Note",
            template_type="soap",
            specialty="cardiology",
            content_template="S: .cc\n\nO: VS: .vs\nECG: .ecg\n\nA: .dx\n\nP: .plan",
            smart_phrases=[{"code": ".cc", "expansion": "Chief Complaint: "}],
            created_by_provider_id=PROVIDER,
            is_shared=True,
            version="1.0",
        )
        assert template.template_type == "soap"
        assert template.is_shared is True

    def test_smart_phrase(self):
        from products.cymed.provider_portal.clinical_documentation.models import SmartPhrase

        phrase = SmartPhrase.objects.create(
            tenant_id=TENANT,
            code=".hpi",
            expansion="History of present illness: Patient presents with ",
            phrase_type="phrase",
            created_by_provider_id=PROVIDER,
            is_personal=True,
            specialty="internal_medicine",
        )
        assert phrase.code == ".hpi"
        assert phrase.is_personal is True

    def test_create_clinical_note(self):
        from products.cymed.provider_portal.clinical_documentation.models import (
            ProviderClinicalNote,
        )

        note = ProviderClinicalNote.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            cymed_encounter_id=uuid.uuid4(),
            author_provider_id=PROVIDER,
            author_name="Dr. Hassan Al-Ahmad",
            author_type="physician",
            note_type="progress",
            note_title="Daily Progress Note",
            note_body="S: Patient reports improvement in chest pain.\nO: Afebrile, BP 130/80.\nA: Stable ACS.\nP: Continue heparin infusion.",
            status="draft",
        )
        assert note.note_type == "progress"
        assert note.status == "draft"
        assert note.is_confidential is False

    def test_sign_clinical_note(self):
        from products.cymed.provider_portal.clinical_documentation.models import (
            ProviderClinicalNote,
        )

        note = ProviderClinicalNote.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            author_provider_id=PROVIDER,
            author_name="Dr. Hassan",
            author_type="physician",
            note_type="soap",
            note_body="Signed note content.",
            status="signed",
            signed_at=timezone.now(),
            signed_by=PROVIDER,
        )
        assert note.status == "signed"
        assert note.signed_by == PROVIDER

    def test_note_cosignature(self):
        from products.cymed.provider_portal.clinical_documentation.models import (
            NoteCoSignature,
            ProviderClinicalNote,
        )

        note = ProviderClinicalNote.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            author_provider_id=uuid.uuid4(),
            author_name="Dr. Layla Resident",
            author_type="physician",
            note_type="progress",
            note_body="Resident note body.",
            status="in_review",
        )
        cosig = NoteCoSignature.objects.create(
            tenant_id=TENANT,
            note=note,
            cosigner_provider_id=PROVIDER,
            cosigner_name="Dr. Hassan (Attending)",
            cosigner_type="physician",
            role="supervisor",
            is_signed=True,
            signed_at=timezone.now(),
        )
        assert cosig.role == "supervisor"
        assert cosig.is_signed is True
        assert note.cosignatures.count() == 1

    def test_ai_note_summary_advisory_only(self):
        """AI can populate ai_summary but cannot sign the note."""
        from products.cymed.provider_portal.clinical_documentation.models import (
            ProviderClinicalNote,
        )

        note = ProviderClinicalNote.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            author_provider_id=PROVIDER,
            author_name="Dr. Hassan",
            author_type="physician",
            note_type="discharge",
            note_body="Discharge note body.",
            status="draft",
            ai_summary="Patient admitted for ACS management. Discharged stable on dual antiplatelet therapy.",
        )
        # AI summary present but note is NOT signed — provider must sign
        assert note.ai_summary != ""
        assert note.status == "draft"
        assert note.signed_by is None


# ──────────────────────────────────────────────────
# ORDERS TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestOrders:
    def test_place_lab_order(self):
        from products.cymed.provider_portal.orders.models import ProviderOrderRequest

        order = ProviderOrderRequest.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            cymed_encounter_id=uuid.uuid4(),
            ordering_provider_id=PROVIDER,
            ordering_provider_name="Dr. Hassan",
            order_category="laboratory",
            order_name="Complete Blood Count with Differential",
            order_details={"test_code": "CBC-DIFF", "priority": "stat"},
            priority="stat",
            status="submitted",
            clinical_indication="Suspected sepsis",
        )
        assert order.order_category == "laboratory"
        assert order.priority == "stat"
        assert order.status == "submitted"

    def test_place_medication_order(self):
        from products.cymed.provider_portal.orders.models import ProviderOrderRequest

        order = ProviderOrderRequest.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordering_provider_id=PROVIDER,
            ordering_provider_name="Dr. Hassan",
            order_category="medication",
            order_name="Metoprolol 25mg PO BID",
            order_details={"rxnorm": "854901", "dose": "25mg", "route": "oral", "frequency": "BID"},
            priority="routine",
            status="submitted",
        )
        assert order.order_category == "medication"

    def test_place_imaging_order(self):
        from products.cymed.provider_portal.orders.models import ProviderOrderRequest

        order = ProviderOrderRequest.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordering_provider_id=PROVIDER,
            ordering_provider_name="Dr. Hassan",
            order_category="imaging",
            order_name="CT Chest without contrast",
            order_details={"modality": "CT", "body_part": "Chest", "contrast": False},
            priority="urgent",
            status="submitted",
            fhir_service_request_id=f"ServiceRequest/{uuid.uuid4()}",
        )
        assert order.order_category == "imaging"
        assert "ServiceRequest/" in order.fhir_service_request_id

    def test_order_modification(self):
        from products.cymed.provider_portal.orders.models import (
            OrderModification,
            ProviderOrderRequest,
        )

        order = ProviderOrderRequest.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordering_provider_id=PROVIDER,
            ordering_provider_name="Dr. Hassan",
            order_category="laboratory",
            order_name="Troponin",
            priority="routine",
            status="submitted",
        )
        mod = OrderModification.objects.create(
            tenant_id=TENANT,
            order=order,
            modified_by_provider_id=PROVIDER,
            modified_by_name="Dr. Hassan",
            modification_type="priority_change",
            previous_value={"priority": "routine"},
            new_value={"priority": "stat"},
            reason="Patient clinically deteriorating, elevating priority.",
        )
        assert mod.modification_type == "priority_change"
        assert mod.previous_value["priority"] == "routine"

    def test_order_set(self):
        from products.cymed.provider_portal.orders.models import OrderSet

        order_set = OrderSet.objects.create(
            tenant_id=TENANT,
            name="ACS Admission Order Set",
            description="Standard orders for ACS admission.",
            specialty="cardiology",
            order_set_type="admission",
            orders=[
                {"order_category": "laboratory", "order_name": "CBC"},
                {"order_category": "laboratory", "order_name": "Troponin"},
                {"order_category": "imaging", "order_name": "ECG"},
                {"order_category": "medication", "order_name": "Aspirin 300mg"},
            ],
            created_by_provider_id=PROVIDER,
            is_shared=True,
            is_active=True,
        )
        assert order_set.order_set_type == "admission"
        assert len(order_set.orders) == 4


# ──────────────────────────────────────────────────
# RESULTS TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestResults:
    def test_create_result_view(self):
        from products.cymed.provider_portal.results.models import ProviderResultView

        result = ProviderResultView.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            result_type="laboratory",
            result_source_id=uuid.uuid4(),
            result_source_type="lab_result",
            result_name="Complete Blood Count",
            result_date=date.today(),
            result_status="final",
            is_critical=False,
            ordering_provider_id=PROVIDER,
            loinc_code="58410-2",
        )
        assert result.result_type == "laboratory"
        assert result.is_reviewed is False

    def test_critical_result_alert(self):
        from products.cymed.provider_portal.results.models import (
            CriticalResultAlert,
            ProviderResultView,
        )

        result = ProviderResultView.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            result_type="laboratory",
            result_source_id=uuid.uuid4(),
            result_source_type="lab_result",
            result_name="Potassium",
            result_date=date.today(),
            result_status="final",
            is_critical=True,
            ordering_provider_id=PROVIDER,
        )
        alert = CriticalResultAlert.objects.create(
            tenant_id=TENANT,
            result=result,
            patient_id=PATIENT,
            alerted_provider_id=PROVIDER,
            alerted_provider_name="Dr. Hassan",
            alert_type="critical_value",
            result_value="6.8 mEq/L",
            normal_range="3.5–5.0 mEq/L",
            clinical_significance="Severe hyperkalemia — risk of cardiac arrhythmia.",
            status="pending",
        )
        assert alert.alert_type == "critical_value"
        assert alert.status == "pending"

    def test_result_acknowledgement(self):
        from products.cymed.provider_portal.results.models import (
            ProviderResultView,
            ResultAcknowledgement,
        )

        result = ProviderResultView.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            result_type="imaging",
            result_source_id=uuid.uuid4(),
            result_source_type="imaging_result",
            result_name="Chest CT Report",
            result_date=date.today(),
            result_status="final",
            ordering_provider_id=PROVIDER,
        )
        ack = ResultAcknowledgement.objects.create(
            tenant_id=TENANT,
            result=result,
            provider_id=PROVIDER,
            provider_name="Dr. Hassan",
            provider_type="physician",
            action_taken="ordered_follow_up",
            action_notes="Ordered pulmonology consult for incidental PE finding.",
            follow_up_date=date.today() + timedelta(days=1),
        )
        assert ack.action_taken == "ordered_follow_up"
        assert result.acknowledgements.count() == 1

    def test_result_trend(self):
        from products.cymed.provider_portal.results.models import ResultTrend

        trend = ResultTrend.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            test_code="TROPONIN_I",
            test_name="Troponin I",
            loinc_code="10839-9",
            unit="ng/mL",
            reference_range_low=0.00,
            reference_range_high=0.04,
            datapoints=[
                {"date": "2026-06-20T08:00", "value": 0.12},
                {"date": "2026-06-20T12:00", "value": 0.45},
                {"date": "2026-06-20T16:00", "value": 0.78},
            ],
        )
        assert trend.test_name == "Troponin I"
        assert len(trend.datapoints) == 3


# ──────────────────────────────────────────────────
# CARE TEAM TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestCareTeam:
    def test_create_care_team(self):
        from products.cymed.provider_portal.care_team.models import CareTeam

        team = CareTeam.objects.create(
            tenant_id=TENANT,
            team_name="Cardiology Team A",
            team_type="primary",
            patient_id=PATIENT,
            unit_id=UNIT_ID,
            specialty="cardiology",
            is_active=True,
            created_by_provider_id=PROVIDER,
        )
        assert team.team_type == "primary"
        assert team.is_active is True

    def test_add_care_team_members(self):
        from products.cymed.provider_portal.care_team.models import CareTeam, CareTeamMember

        team = CareTeam.objects.create(
            tenant_id=TENANT,
            team_name="ICU Team",
            team_type="multidisciplinary",
            unit_id=UNIT_ID,
            created_by_provider_id=PROVIDER,
        )
        attending = CareTeamMember.objects.create(
            tenant_id=TENANT,
            care_team=team,
            provider_id=PROVIDER,
            provider_name="Dr. Hassan",
            provider_type="physician",
            role="attending",
            is_primary=True,
            is_active=True,
            added_by=PROVIDER,
        )
        pharmacist = CareTeamMember.objects.create(
            tenant_id=TENANT,
            care_team=team,
            provider_id=uuid.uuid4(),
            provider_name="PharmD Fatima",
            provider_type="clinical_pharmacist",
            role="pharmacist",
            is_primary=False,
            is_active=True,
            added_by=PROVIDER,
        )
        assert team.members.count() == 2
        assert attending.role == "attending"
        assert pharmacist.role == "pharmacist"

    def test_care_team_assignment(self):
        from products.cymed.provider_portal.care_team.models import CareTeam, CareTeamAssignment

        team = CareTeam.objects.create(
            tenant_id=TENANT,
            team_name="MDT Team",
            team_type="multidisciplinary",
            created_by_provider_id=PROVIDER,
        )
        assignment = CareTeamAssignment.objects.create(
            tenant_id=TENANT,
            care_team=team,
            patient_id=PATIENT,
            cymed_encounter_id=uuid.uuid4(),
            is_active=True,
            assignment_reason="Multi-specialty care required.",
            assigned_by=PROVIDER,
        )
        assert assignment.is_active is True

    def test_coverage_schedule(self):
        from products.cymed.provider_portal.care_team.models import CareTeam, CoverageSchedule

        team = CareTeam.objects.create(
            tenant_id=TENANT,
            team_name="On-Call Team",
            team_type="on_call",
            created_by_provider_id=PROVIDER,
        )
        coverage = CoverageSchedule.objects.create(
            tenant_id=TENANT,
            care_team=team,
            covering_provider_id=PROVIDER_2,
            covering_provider_name="Dr. Layla",
            covered_provider_id=PROVIDER,
            coverage_date=date.today(),
            coverage_start=time(18, 0),
            coverage_end=time(8, 0),
            coverage_type="on_call",
            is_active=True,
        )
        assert coverage.coverage_type == "on_call"


# ──────────────────────────────────────────────────
# APPROVALS TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestApprovals:
    def test_create_approval_request(self):
        from products.cymed.provider_portal.approvals.models import ApprovalRequest

        req = ApprovalRequest.objects.create(
            tenant_id=TENANT,
            approval_type="controlled_substance",
            title="Morphine 10mg IV PRN for post-op pain",
            description="Patient post CABG, requesting controlled substance order approval.",
            requested_by_provider_id=PROVIDER,
            requested_by_name="Dr. Layla (Resident)",
            approver_id=PROVIDER_2,
            approver_name="Dr. Hassan (Attending)",
            patient_id=PATIENT,
            priority="urgent",
            status="pending",
        )
        assert req.approval_type == "controlled_substance"
        assert req.status == "pending"

    def test_approve_request(self):
        from products.cymed.provider_portal.approvals.models import (
            ApprovalDecision,
            ApprovalRequest,
        )

        req = ApprovalRequest.objects.create(
            tenant_id=TENANT,
            approval_type="medication_approval",
            title="Off-formulary drug approval",
            description="Requesting Apixaban (off-formulary) for AFib.",
            requested_by_provider_id=PROVIDER,
            requested_by_name="Dr. Hassan",
            approver_id=PROVIDER_2,
            approver_name="Dr. Chief",
            status="approved",
            decided_at=timezone.now(),
        )
        decision = ApprovalDecision.objects.create(
            tenant_id=TENANT,
            approval_request=req,
            decided_by_provider_id=PROVIDER_2,
            decided_by_name="Dr. Chief",
            decision="approved",
            decision_notes="Clinically justified. Patient has contraindication to warfarin.",
        )
        assert decision.decision == "approved"
        assert req.decisions.count() == 1

    def test_rejection_with_reason(self):
        from products.cymed.provider_portal.approvals.models import ApprovalRequest

        req = ApprovalRequest.objects.create(
            tenant_id=TENANT,
            approval_type="leave_request",
            title="Annual Leave 2 weeks",
            description="Requesting 2 weeks annual leave during Eid.",
            requested_by_provider_id=PROVIDER,
            requested_by_name="Dr. Mohammed",
            approver_id=PROVIDER_2,
            approver_name="Head of Department",
            status="rejected",
            rejection_reason="Insufficient coverage during requested period. Please reschedule.",
            decided_at=timezone.now(),
        )
        assert req.status == "rejected"
        assert "reschedule" in req.rejection_reason

    def test_approval_audit_log(self):
        from products.cymed.provider_portal.approvals.models import (
            ApprovalAuditLog,
            ApprovalRequest,
        )

        req = ApprovalRequest.objects.create(
            tenant_id=TENANT,
            approval_type="administrative",
            title="Schedule change request",
            requested_by_provider_id=PROVIDER,
            requested_by_name="Dr. Hassan",
            approver_id=PROVIDER_2,
            approver_name="Admin",
            status="pending",
        )
        log = ApprovalAuditLog.objects.create(
            tenant_id=TENANT,
            approval_request=req,
            action="submitted",
            performed_by_provider_id=PROVIDER,
            performed_by_name="Dr. Hassan",
            details={"submitted_via": "mobile_app"},
            ip_address="192.168.1.100",
        )
        assert log.action == "submitted"
        assert req.audit_log.count() == 1


# ──────────────────────────────────────────────────
# TELEMEDICINE TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestProviderTelemedicine:
    def test_create_provider_session(self):
        from products.cymed.provider_portal.telemedicine.models import ProviderTelemedicineSession

        session = ProviderTelemedicineSession.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            provider_id=PROVIDER,
            provider_name="Dr. Hassan",
            provider_type="physician",
            session_type="video",
            visit_type="follow_up",
            status="scheduled",
            scheduled_at=timezone.now() + timedelta(hours=2),
            meeting_url="https://meet.cymed.health/prov/abc123",
        )
        assert session.session_type == "video"
        assert session.visit_type == "follow_up"

    def test_consult_request(self):
        from products.cymed.provider_portal.telemedicine.models import ConsultRequest

        consult = ConsultRequest.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            requesting_provider_id=PROVIDER,
            requesting_provider_name="Dr. Hassan (Internist)",
            consulting_specialty="cardiology",
            urgency="urgent",
            consult_reason="Patient with new-onset AFib requiring cardiology input.",
            status="pending",
        )
        assert consult.urgency == "urgent"
        assert consult.status == "pending"

    def test_second_opinion_request(self):
        from products.cymed.provider_portal.telemedicine.models import SecondOpinionRequest

        opinion = SecondOpinionRequest.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            requesting_provider_id=PROVIDER,
            requested_specialty="oncology",
            clinical_question="Is this mediastinal mass consistent with lymphoma? Recommend treatment approach.",
            urgency="routine",
            status="pending",
            attached_records=[
                {
                    "record_type": "imaging",
                    "record_id": str(uuid.uuid4()),
                    "record_title": "CT Chest",
                },
                {
                    "record_type": "lab_result",
                    "record_id": str(uuid.uuid4()),
                    "record_title": "LDH Level",
                },
            ],
        )
        assert opinion.urgency == "routine"
        assert len(opinion.attached_records) == 2
