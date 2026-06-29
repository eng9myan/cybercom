"""
CyMed Provider Portal — Workspace, Patient Lists, Workforce Tests (Phase 3.7)
"""

import uuid
from datetime import date, time, timedelta

import pytest

TENANT = uuid.uuid4()
PROVIDER = uuid.uuid4()
PATIENT = uuid.uuid4()
OTHER_TENANT = uuid.uuid4()
UNIT_ID = uuid.uuid4()


# ──────────────────────────────────────────────────
# WORKSPACE TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestProviderWorkspace:
    def test_create_workspace(self):
        from products.cymed.provider_portal.workspace.models import ProviderWorkspace

        ws = ProviderWorkspace.objects.create(
            tenant_id=TENANT,
            provider_id=PROVIDER,
            provider_type="physician",
            cyidentity_user_id=uuid.uuid4(),
            is_active=True,
            preferred_specialty="cardiology",
            department="Internal Medicine",
        )
        assert ws.provider_type == "physician"
        assert ws.is_active is True
        assert ws.language == "en"

    def test_provider_dashboard(self):
        from products.cymed.provider_portal.workspace.models import (
            ProviderDashboard,
            ProviderWorkspace,
        )

        ws = ProviderWorkspace.objects.create(
            tenant_id=TENANT,
            provider_id=uuid.uuid4(),
            provider_type="nurse",
            cyidentity_user_id=uuid.uuid4(),
        )
        dashboard = ProviderDashboard.objects.create(
            tenant_id=TENANT,
            workspace=ws,
            layout_config={"tasks": {"x": 0, "y": 0, "w": 6, "h": 4}},
            show_tasks=True,
            show_results=True,
            show_census=True,
        )
        assert dashboard.show_tasks is True
        assert dashboard.workspace == ws

    def test_provider_preferences(self):
        from products.cymed.provider_portal.workspace.models import (
            ProviderPreferences,
            ProviderWorkspace,
        )

        ws = ProviderWorkspace.objects.create(
            tenant_id=TENANT,
            provider_id=uuid.uuid4(),
            provider_type="pharmacist",
            cyidentity_user_id=uuid.uuid4(),
        )
        prefs = ProviderPreferences.objects.create(
            tenant_id=TENANT,
            workspace=ws,
            default_note_template="SOAP",
            result_critical_alert_sound=True,
            ai_suggestions_enabled=True,
            voice_dictation_enabled=False,
        )
        assert prefs.result_critical_alert_sound is True
        assert prefs.voice_dictation_enabled is False

    def test_workspace_session(self):
        from products.cymed.provider_portal.workspace.models import (
            ProviderWorkspace,
            WorkspaceSession,
        )

        ws = ProviderWorkspace.objects.create(
            tenant_id=TENANT,
            provider_id=uuid.uuid4(),
            provider_type="radiologist",
            cyidentity_user_id=uuid.uuid4(),
        )
        session = WorkspaceSession.objects.create(
            tenant_id=TENANT,
            workspace=ws,
            session_token="tok_abc123",
            device_type="desktop",
            ip_address="192.168.1.100",
            is_active=True,
        )
        assert session.device_type == "desktop"
        assert session.is_active is True
        assert ws.sessions.count() == 1

    def test_all_provider_types(self):
        from products.cymed.provider_portal.workspace.models import ProviderWorkspace

        provider_types = [
            "physician",
            "consultant",
            "resident",
            "nurse",
            "charge_nurse",
            "pharmacist",
            "clinical_pharmacist",
            "radiologist",
            "lab_technologist",
            "microbiologist",
            "pathologist",
            "therapist",
            "care_coordinator",
            "administrator",
        ]
        for i, ptype in enumerate(provider_types):
            ws = ProviderWorkspace.objects.create(
                tenant_id=TENANT,
                provider_id=uuid.uuid4(),
                provider_type=ptype,
                cyidentity_user_id=uuid.uuid4(),
            )
            assert ws.provider_type == ptype
        assert ProviderWorkspace.objects.filter(tenant_id=TENANT).count() == len(provider_types)

    def test_workspace_tenant_isolation(self):
        from products.cymed.provider_portal.workspace.models import ProviderWorkspace

        ProviderWorkspace.objects.create(
            tenant_id=TENANT,
            provider_id=uuid.uuid4(),
            provider_type="physician",
            cyidentity_user_id=uuid.uuid4(),
        )
        ProviderWorkspace.objects.create(
            tenant_id=OTHER_TENANT,
            provider_id=uuid.uuid4(),
            provider_type="nurse",
            cyidentity_user_id=uuid.uuid4(),
        )
        assert ProviderWorkspace.objects.filter(tenant_id=TENANT).count() == 1
        assert ProviderWorkspace.objects.filter(tenant_id=OTHER_TENANT).count() == 1


# ──────────────────────────────────────────────────
# PATIENT LISTS TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestPatientLists:
    def test_create_patient_list(self):
        from products.cymed.provider_portal.patient_lists.models import PatientList

        pl = PatientList.objects.create(
            tenant_id=TENANT,
            name="Dr. Hassan's Patients",
            list_type="my_patients",
            workspace_id=uuid.uuid4(),
            is_active=True,
            sort_order="acuity",
        )
        assert pl.list_type == "my_patients"
        assert pl.sort_order == "acuity"

    def test_patient_assignment(self):
        from products.cymed.provider_portal.patient_lists.models import (
            PatientAssignment,
            PatientList,
        )

        pl = PatientList.objects.create(
            tenant_id=TENANT,
            name="Ward 4B",
            list_type="ward",
            workspace_id=uuid.uuid4(),
        )
        assignment = PatientAssignment.objects.create(
            tenant_id=TENANT,
            patient_list=pl,
            patient_id=PATIENT,
            cymed_encounter_id=uuid.uuid4(),
            bed_number="4B-12",
            unit_name="Cardiology Ward 4B",
            admission_date=date.today() - timedelta(days=3),
            acuity_score=3,
            is_primary=True,
            is_active=True,
        )
        assert assignment.acuity_score == 3
        assert assignment.bed_number == "4B-12"
        assert pl.assignments.count() == 1

    def test_provider_assignment(self):
        from django.utils import timezone

        from products.cymed.provider_portal.patient_lists.models import ProviderAssignment

        assignment = ProviderAssignment.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            provider_id=PROVIDER,
            provider_type="physician",
            role="attending",
            unit_id=UNIT_ID,
            is_primary=True,
            effective_from=timezone.now(),
            coverage_type="scheduled",
        )
        assert assignment.role == "attending"
        assert assignment.is_primary is True

    def test_patient_census(self):
        from products.cymed.provider_portal.patient_lists.models import PatientCensus

        census = PatientCensus.objects.create(
            tenant_id=TENANT,
            unit_id=UNIT_ID,
            unit_name="Cardiology Ward 4B",
            census_date=date.today(),
            total_beds=30,
            occupied_beds=24,
            available_beds=6,
            pending_admissions=2,
            pending_discharges=3,
            average_acuity=3.2,
        )
        assert census.occupied_beds == 24
        assert census.available_beds == 6
        assert census.total_beds == 30

    def test_icu_patient_list(self):
        from products.cymed.provider_portal.patient_lists.models import PatientList

        icu = PatientList.objects.create(
            tenant_id=TENANT,
            name="ICU Patients",
            list_type="icu",
            workspace_id=uuid.uuid4(),
            unit_id=UNIT_ID,
            auto_populate=True,
        )
        assert icu.list_type == "icu"
        assert icu.auto_populate is True


# ──────────────────────────────────────────────────
# CLINICAL TASKS TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestClinicalTasks:
    def test_create_clinical_task(self):
        from products.cymed.provider_portal.clinical_tasks.models import ClinicalTask

        task = ClinicalTask.objects.create(
            tenant_id=TENANT,
            task_type="critical_result_review",
            title="Review critical potassium result for patient",
            patient_id=PATIENT,
            priority="stat",
            status="pending",
            assigned_to_provider_id=PROVIDER,
            assigned_to_type="physician",
            created_by_provider_id=uuid.uuid4(),
            source_type="lab_result",
            source_id=uuid.uuid4(),
        )
        assert task.priority == "stat"
        assert task.status == "pending"
        assert task.task_type == "critical_result_review"

    def test_task_assignment(self):
        from products.cymed.provider_portal.clinical_tasks.models import (
            ClinicalTask,
            TaskAssignment,
        )

        task = ClinicalTask.objects.create(
            tenant_id=TENANT,
            task_type="wound_care",
            title="Wound care for patient bed 4B-12",
            patient_id=PATIENT,
            priority="routine",
            status="pending",
            assigned_to_provider_id=PROVIDER,
            assigned_to_type="nurse",
            created_by_provider_id=uuid.uuid4(),
        )
        ta = TaskAssignment.objects.create(
            tenant_id=TENANT,
            task=task,
            provider_id=PROVIDER,
            provider_type="nurse",
            assigned_by=uuid.uuid4(),
            assignment_type="primary",
            is_active=True,
        )
        assert ta.assignment_type == "primary"
        assert task.assignments.count() == 1

    def test_task_comment(self):
        from products.cymed.provider_portal.clinical_tasks.models import ClinicalTask, TaskComment

        task = ClinicalTask.objects.create(
            tenant_id=TENANT,
            task_type="medication_review",
            title="Medication reconciliation on admission",
            patient_id=PATIENT,
            priority="urgent",
            status="in_progress",
            assigned_to_provider_id=PROVIDER,
            assigned_to_type="clinical_pharmacist",
            created_by_provider_id=uuid.uuid4(),
        )
        comment = TaskComment.objects.create(
            tenant_id=TENANT,
            task=task,
            author_provider_id=PROVIDER,
            author_name="Dr. Khaled Al-Ahmad",
            comment_text="Started medication reconciliation. Found 3 discrepancies.",
        )
        assert comment.is_system_comment is False
        assert task.comments.count() == 1

    def test_task_escalation(self):

        from products.cymed.provider_portal.clinical_tasks.models import (
            ClinicalTask,
            TaskEscalation,
        )

        task = ClinicalTask.objects.create(
            tenant_id=TENANT,
            task_type="patient_callback",
            title="Urgent patient callback - deteriorating vitals",
            patient_id=PATIENT,
            priority="urgent",
            status="escalated",
            assigned_to_provider_id=PROVIDER,
            assigned_to_type="physician",
            created_by_provider_id=uuid.uuid4(),
        )
        escalation = TaskEscalation.objects.create(
            tenant_id=TENANT,
            task=task,
            escalated_by_provider_id=uuid.uuid4(),
            escalated_to_provider_id=PROVIDER,
            escalation_reason="Patient vitals deteriorating, immediate attention required.",
            previous_priority="routine",
            new_priority="stat",
        )
        assert escalation.new_priority == "stat"
        assert escalation.previous_priority == "routine"


# ──────────────────────────────────────────────────
# CLINICAL MESSAGING TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestClinicalMessaging:
    def test_create_message_thread(self):
        from products.cymed.provider_portal.clinical_messaging.models import ClinicalMessageThread

        thread = ClinicalMessageThread.objects.create(
            tenant_id=TENANT,
            thread_type="consult_request",
            subject="Cardiology consult request for patient",
            patient_id=PATIENT,
            status="active",
            is_urgent=True,
            created_by_provider_id=PROVIDER,
        )
        assert thread.thread_type == "consult_request"
        assert thread.is_urgent is True

    def test_send_clinical_message(self):
        from products.cymed.provider_portal.clinical_messaging.models import (
            ClinicalMessage,
            ClinicalMessageThread,
        )

        thread = ClinicalMessageThread.objects.create(
            tenant_id=TENANT,
            thread_type="direct",
            subject="Quick question about anticoagulation",
            created_by_provider_id=PROVIDER,
            status="active",
        )
        msg = ClinicalMessage.objects.create(
            tenant_id=TENANT,
            thread=thread,
            sender_provider_id=PROVIDER,
            sender_name="Dr. Hassan Al-Ahmad",
            sender_type="physician",
            body="Can we switch this patient to NOAC instead of warfarin?",
            priority="routine",
        )
        assert msg.is_read is False
        assert thread.messages.count() == 1

    def test_clinical_group(self):
        from products.cymed.provider_portal.clinical_messaging.models import ClinicalGroup

        group = ClinicalGroup.objects.create(
            tenant_id=TENANT,
            name="Cardiology On-Call Team",
            group_type="on_call",
            members=[
                {
                    "provider_id": str(uuid.uuid4()),
                    "provider_name": "Dr. Hassan",
                    "role": "attending",
                },
                {
                    "provider_id": str(uuid.uuid4()),
                    "provider_name": "Dr. Layla",
                    "role": "resident",
                },
            ],
            admin_provider_id=PROVIDER,
            message_retention_days=365,
        )
        assert group.group_type == "on_call"
        assert len(group.members) == 2

    def test_message_participant(self):
        from products.cymed.provider_portal.clinical_messaging.models import (
            ClinicalMessageThread,
            MessageThreadParticipant,
        )

        thread = ClinicalMessageThread.objects.create(
            tenant_id=TENANT,
            thread_type="team",
            subject="ICU Handoff",
            created_by_provider_id=PROVIDER,
            status="active",
        )
        participant = MessageThreadParticipant.objects.create(
            tenant_id=TENANT,
            thread=thread,
            provider_id=PROVIDER,
            provider_name="Dr. Hassan",
            provider_type="physician",
            is_active=True,
        )
        assert participant.is_active is True
        assert thread.participants.count() == 1


# ──────────────────────────────────────────────────
# WORKFORCE TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestWorkforce:
    def test_provider_schedule(self):
        from products.cymed.provider_portal.workforce.models import ProviderSchedule

        schedule = ProviderSchedule.objects.create(
            tenant_id=TENANT,
            provider_id=PROVIDER,
            provider_type="nurse",
            provider_name="Nurse Fatima Al-Zahra",
            unit_id=UNIT_ID,
            unit_name="Ward 4B",
            schedule_date=date.today(),
            shift_type="morning",
            shift_start=time(7, 0),
            shift_end=time(15, 0),
            status="confirmed",
        )
        assert schedule.shift_type == "morning"
        assert schedule.status == "confirmed"

    def test_leave_request(self):
        from products.cymed.provider_portal.workforce.models import LeaveRequest

        leave = LeaveRequest.objects.create(
            tenant_id=TENANT,
            provider_id=PROVIDER,
            provider_name="Dr. Mohammed Al-Nsour",
            leave_type="annual",
            start_date=date.today() + timedelta(days=14),
            end_date=date.today() + timedelta(days=20),
            total_days=5,
            status="pending",
            reason="Annual family vacation.",
        )
        assert leave.leave_type == "annual"
        assert leave.status == "pending"
        assert leave.total_days == 5

    def test_attendance_record(self):
        from products.cymed.provider_portal.workforce.models import AttendanceRecord

        att = AttendanceRecord.objects.create(
            tenant_id=TENANT,
            provider_id=PROVIDER,
            provider_name="Dr. Hassan",
            attendance_date=date.today(),
            check_in_time=time(7, 2),
            check_out_time=time(15, 10),
            actual_hours=8.13,
            status="present",
        )
        assert att.status == "present"

    def test_credential_expiry(self):
        from products.cymed.provider_portal.workforce.models import CredentialExpiry

        cred = CredentialExpiry.objects.create(
            tenant_id=TENANT,
            provider_id=PROVIDER,
            provider_name="Dr. Hassan",
            credential_type="bls",
            credential_name="Basic Life Support Certification",
            expiry_date=date.today() + timedelta(days=20),
            days_until_expiry=20,
            alert_status="expiring_soon",
            is_acknowledged=False,
        )
        assert cred.alert_status == "expiring_soon"
        assert cred.is_acknowledged is False


# ──────────────────────────────────────────────────
# ROUNDING TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestRounding:
    def test_create_clinical_round(self):

        from products.cymed.provider_portal.rounding.models import ClinicalRound

        rnd = ClinicalRound.objects.create(
            tenant_id=TENANT,
            round_type="ward",
            unit_id=UNIT_ID,
            unit_name="Cardiology Ward 4B",
            attending_provider_id=PROVIDER,
            attending_name="Dr. Hassan Al-Ahmad",
            round_date=date.today(),
            scheduled_time=time(8, 0),
            status="scheduled",
            patient_count=12,
        )
        assert rnd.round_type == "ward"
        assert rnd.status == "scheduled"

    def test_round_team(self):

        from products.cymed.provider_portal.rounding.models import ClinicalRound, RoundTeam

        rnd = ClinicalRound.objects.create(
            tenant_id=TENANT,
            round_type="multidisciplinary",
            unit_id=UNIT_ID,
            unit_name="ICU",
            attending_provider_id=PROVIDER,
            attending_name="Dr. Hassan",
            round_date=date.today(),
            status="in_progress",
        )
        team_member = RoundTeam.objects.create(
            tenant_id=TENANT,
            round=rnd,
            provider_id=uuid.uuid4(),
            provider_name="Dr. Layla Resident",
            provider_type="physician",
            role="resident",
            is_present=True,
        )
        assert team_member.role == "resident"
        assert team_member.is_present is True

    def test_round_finding_and_action(self):
        from products.cymed.provider_portal.rounding.models import (
            ClinicalRound,
            RoundAction,
            RoundFinding,
        )

        rnd = ClinicalRound.objects.create(
            tenant_id=TENANT,
            round_type="icu",
            unit_id=UNIT_ID,
            unit_name="ICU",
            attending_provider_id=PROVIDER,
            attending_name="Dr. Hassan",
            round_date=date.today(),
            status="in_progress",
        )
        finding = RoundFinding.objects.create(
            tenant_id=TENANT,
            round=rnd,
            patient_id=PATIENT,
            finding_type="vital_sign_concern",
            finding_text="BP trending upward: 160/95 → 170/100 → 180/105 over 6 hours.",
            severity="urgent",
            recorded_by_provider_id=PROVIDER,
            recorded_by_name="Dr. Hassan",
            requires_action=True,
        )
        action = RoundAction.objects.create(
            tenant_id=TENANT,
            round=rnd,
            finding=finding,
            patient_id=PATIENT,
            action_type="order_placed",
            action_description="Ordered IV antihypertensive.",
            assigned_to_provider_id=PROVIDER,
            assigned_to_name="Dr. Hassan",
            status="pending",
        )
        assert finding.severity == "urgent"
        assert action.action_type == "order_placed"
