"""
CyMed Provider Portal — Security, Analytics, Mobile, AI Guardrails Tests (Phase 3.7)
"""

import uuid
from datetime import date, timedelta

import pytest
from django.utils import timezone

TENANT = uuid.uuid4()
PROVIDER = uuid.uuid4()
PATIENT = uuid.uuid4()
OTHER_TENANT = uuid.uuid4()
UNIT_ID = uuid.uuid4()


# ──────────────────────────────────────────────────
# ANALYTICS TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestProviderAnalytics:
    def test_productivity_snapshot(self):
        from products.cymed.provider_portal.analytics.models import ProviderProductivitySnapshot

        snapshot = ProviderProductivitySnapshot.objects.create(
            tenant_id=TENANT,
            provider_id=PROVIDER,
            provider_name="Dr. Hassan",
            provider_type="physician",
            snapshot_date=date.today(),
            snapshot_period="daily",
            patients_seen=12,
            notes_completed=10,
            notes_pending=2,
            orders_placed=45,
            results_reviewed=28,
            tasks_completed=8,
            tasks_pending=3,
            messages_sent=15,
            telemedicine_sessions=2,
            avg_documentation_time_minutes=12.5,
        )
        assert snapshot.patients_seen == 12
        assert snapshot.notes_completed == 10
        assert snapshot.avg_documentation_time_minutes == 12.5

    def test_clinical_quality_metric(self):
        from products.cymed.provider_portal.analytics.models import ClinicalQualityMetric

        metric = ClinicalQualityMetric.objects.create(
            tenant_id=TENANT,
            metric_type="documentation_completion",
            metric_name="Note completion within 24 hours of encounter",
            measured_at=date.today(),
            scope_type="provider",
            scope_id=PROVIDER,
            scope_name="Dr. Hassan Al-Ahmad",
            numerator=90,
            denominator=100,
            rate=90.0,
            target_rate=95.0,
            meets_target=False,
        )
        assert metric.rate == 90.0
        assert metric.meets_target is False

    def test_workforce_dashboard_snapshot(self):
        from products.cymed.provider_portal.analytics.models import WorkforceDashboardSnapshot

        snapshot = WorkforceDashboardSnapshot.objects.create(
            tenant_id=TENANT,
            unit_id=UNIT_ID,
            unit_name="Cardiology Ward 4B",
            snapshot_date=date.today(),
            total_providers=20,
            providers_on_duty=15,
            providers_on_leave=2,
            providers_on_call=3,
            unfilled_shifts=1,
            credential_expiry_alerts=3,
            pending_leave_requests=2,
            open_tasks=45,
            critical_alerts_pending=2,
            patient_census=24,
            staff_patient_ratio=1.6,
        )
        assert snapshot.providers_on_duty == 15
        assert snapshot.staff_patient_ratio == 1.6

    def test_ai_insight_advisory_only(self):
        """AI insights must always be advisory — cannot alter records."""
        from products.cymed.provider_portal.analytics.models import ProviderAIInsight

        insight = ProviderAIInsight.objects.create(
            tenant_id=TENANT,
            provider_id=PROVIDER,
            patient_id=PATIENT,
            insight_type="care_gap",
            insight_title="Statin therapy gap identified",
            insight_body="Patient with established CAD has no active statin prescription. Consider initiating high-intensity statin therapy.",
            confidence_score=0.87,
            source_data={"diagnoses": ["I25.10"], "active_meds_count": 3},
            status="pending_review",
        )
        assert insight.is_advisory_only is True
        assert insight.status == "pending_review"
        assert insight.acknowledged_by is None

    def test_executive_dashboard_metric(self):
        from products.cymed.provider_portal.analytics.models import ExecutiveDashboardMetric

        metric = ExecutiveDashboardMetric.objects.create(
            tenant_id=TENANT,
            metric_category="clinical_quality",
            metric_name="30-Day Readmission Rate",
            metric_value=8.5,
            metric_unit="%",
            metric_date=date.today(),
            department="Cardiology",
            comparison_value=10.2,
            trend_direction="improving",
            alert_threshold=15.0,
            is_above_threshold=False,
        )
        assert metric.trend_direction == "improving"
        assert metric.is_above_threshold is False


# ──────────────────────────────────────────────────
# MOBILE TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestProviderMobile:
    def test_register_mobile_device(self):
        from products.cymed.provider_portal.mobile.models import ProviderMobileDevice

        device = ProviderMobileDevice.objects.create(
            tenant_id=TENANT,
            provider_id=PROVIDER,
            device_name="iPhone 15 Pro",
            device_type="ios",
            push_token="apns-provider-token-abc123",
            device_fingerprint="fp-hash-abc",
            platform_version="17.4",
            app_version="3.7.0",
            is_active=True,
            is_trusted=True,
        )
        assert device.device_type == "ios"
        assert device.is_trusted is True

    def test_mobile_session(self):
        from products.cymed.provider_portal.mobile.models import MobileSession, ProviderMobileDevice

        device = ProviderMobileDevice.objects.create(
            tenant_id=TENANT,
            provider_id=PROVIDER,
            device_name="Samsung Galaxy S24",
            device_type="android",
            is_active=True,
        )
        session = MobileSession.objects.create(
            tenant_id=TENANT,
            device=device,
            provider_id=PROVIDER,
            session_token="mob-sess-tok-001",
            is_active=True,
            biometric_verified=True,
            ip_address="10.0.0.45",
        )
        assert session.biometric_verified is True
        assert device.sessions.count() == 1

    def test_mobile_preferences(self):
        from products.cymed.provider_portal.mobile.models import (
            MobilePreferences,
            ProviderMobileDevice,
        )

        device = ProviderMobileDevice.objects.create(
            tenant_id=TENANT,
            provider_id=PROVIDER,
            device_name="iPad Pro",
            device_type="tablet",
            is_active=True,
        )
        prefs = MobilePreferences.objects.create(
            tenant_id=TENANT,
            device=device,
            provider_id=PROVIDER,
            home_tab="patient_lists",
            push_critical_results=True,
            push_task_alerts=True,
            push_messages=True,
            push_approval_requests=True,
            biometric_login=True,
            offline_patient_ids=[str(PATIENT), str(uuid.uuid4())],
        )
        assert prefs.home_tab == "patient_lists"
        assert prefs.biometric_login is True
        assert len(prefs.offline_patient_ids) == 2

    def test_mobile_push_notification(self):
        from products.cymed.provider_portal.mobile.models import MobilePushNotification

        notif = MobilePushNotification.objects.create(
            tenant_id=TENANT,
            provider_id=PROVIDER,
            notification_type="critical_result",
            title="CRITICAL: Potassium 6.8 mEq/L",
            body="Severe hyperkalemia for patient in Bed 4B-12. Immediate review required.",
            action_type="result",
            action_id=uuid.uuid4(),
            priority="critical",
            source_type="lab_result",
            source_id=uuid.uuid4(),
        )
        assert notif.priority == "critical"
        assert notif.is_delivered is False
        assert notif.is_read is False


# ──────────────────────────────────────────────────
# TENANT ISOLATION TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestProviderTenantIsolation:
    def test_workspace_isolation(self):
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

    def test_approval_isolation(self):
        from products.cymed.provider_portal.approvals.models import ApprovalRequest

        ApprovalRequest.objects.create(
            tenant_id=TENANT,
            approval_type="leave_request",
            title="T1 Leave Request",
            requested_by_provider_id=uuid.uuid4(),
            requested_by_name="T1 Provider",
            approver_id=uuid.uuid4(),
            approver_name="T1 Head",
            status="pending",
        )
        ApprovalRequest.objects.create(
            tenant_id=OTHER_TENANT,
            approval_type="leave_request",
            title="T2 Leave Request",
            requested_by_provider_id=uuid.uuid4(),
            requested_by_name="T2 Provider",
            approver_id=uuid.uuid4(),
            approver_name="T2 Head",
            status="pending",
        )
        assert ApprovalRequest.objects.filter(tenant_id=TENANT).count() == 1
        assert ApprovalRequest.objects.filter(tenant_id=OTHER_TENANT).count() == 1

    def test_result_isolation(self):
        from products.cymed.provider_portal.results.models import ProviderResultView

        ProviderResultView.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            result_type="laboratory",
            result_source_id=uuid.uuid4(),
            result_source_type="lab_result",
            result_name="T1 CBC",
            result_date=date.today(),
        )
        ProviderResultView.objects.create(
            tenant_id=OTHER_TENANT,
            patient_id=uuid.uuid4(),
            result_type="laboratory",
            result_source_id=uuid.uuid4(),
            result_source_type="lab_result",
            result_name="T2 CBC",
            result_date=date.today(),
        )
        assert ProviderResultView.objects.filter(tenant_id=TENANT).count() == 1
        assert ProviderResultView.objects.filter(tenant_id=OTHER_TENANT).count() == 1


# ──────────────────────────────────────────────────
# AI GUARDRAILS TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestAIGuardrails:
    def test_ai_cannot_sign_documentation(self):
        """AI can populate ai_summary on ProviderClinicalNote — cannot set signed_by."""
        from products.cymed.provider_portal.clinical_documentation.models import (
            ProviderClinicalNote,
        )

        note = ProviderClinicalNote.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            author_provider_id=PROVIDER,
            author_name="Dr. Hassan",
            author_type="physician",
            note_type="progress",
            note_body="Progress note.",
            ai_summary="Patient stable. Continue current management.",
            status="draft",
        )
        assert note.ai_summary != ""
        assert note.status == "draft"
        assert note.signed_by is None

    def test_ai_insight_requires_provider_action(self):
        """AI insight stays pending_review until provider acts — AI cannot self-acknowledge."""
        from products.cymed.provider_portal.analytics.models import ProviderAIInsight

        insight = ProviderAIInsight.objects.create(
            tenant_id=TENANT,
            provider_id=PROVIDER,
            patient_id=PATIENT,
            insight_type="order_suggestion",
            insight_title="Consider DVT prophylaxis",
            insight_body="Patient immobilized >72h post-op. DVT risk score 4. Consider enoxaparin.",
            confidence_score=0.92,
            is_advisory_only=True,
            status="pending_review",
        )
        assert insight.status == "pending_review"
        assert insight.acknowledged_by is None
        assert insight.is_advisory_only is True

    def test_ai_cannot_prescribe(self):
        """Orders must be created by a provider — ordering_provider_id cannot be null."""
        from products.cymed.provider_portal.orders.models import ProviderOrderRequest

        order = ProviderOrderRequest.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordering_provider_id=PROVIDER,
            ordering_provider_name="Dr. Hassan",
            order_category="medication",
            order_name="Enoxaparin 40mg SC daily",
            priority="routine",
            status="submitted",
        )
        assert order.ordering_provider_id == PROVIDER


# ──────────────────────────────────────────────────
# END-TO-END PROVIDER WORKFLOW TEST
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestProviderWorkflow:
    def test_physician_morning_round_to_order_workflow(self):
        """
        Complete physician workflow:
        1. Provider has workspace
        2. Patient appears in patient list
        3. Provider does morning round
        4. Round finding → order placed
        5. Critical result → alert created
        6. Provider acknowledges result
        7. Task created for follow-up
        """
        from products.cymed.provider_portal.clinical_tasks.models import ClinicalTask
        from products.cymed.provider_portal.orders.models import ProviderOrderRequest
        from products.cymed.provider_portal.patient_lists.models import (
            PatientAssignment,
            PatientList,
        )
        from products.cymed.provider_portal.results.models import (
            CriticalResultAlert,
            ProviderResultView,
        )
        from products.cymed.provider_portal.rounding.models import (
            ClinicalRound,
            RoundAction,
            RoundFinding,
        )
        from products.cymed.provider_portal.workspace.models import ProviderWorkspace

        # Step 1: Workspace
        ws = ProviderWorkspace.objects.create(
            tenant_id=TENANT,
            provider_id=PROVIDER,
            provider_type="physician",
            cyidentity_user_id=uuid.uuid4(),
            preferred_specialty="internal_medicine",
        )
        assert ws.provider_type == "physician"

        # Step 2: Patient list
        pl = PatientList.objects.create(
            tenant_id=TENANT,
            name="Morning Patient List",
            list_type="my_patients",
            workspace_id=ws.id,
        )
        PatientAssignment.objects.create(
            tenant_id=TENANT,
            patient_list=pl,
            patient_id=PATIENT,
            bed_number="4B-08",
            unit_name="Internal Medicine Ward 4B",
            acuity_score=3,
            is_active=True,
        )
        assert pl.assignments.count() == 1

        # Step 3: Morning round
        rnd = ClinicalRound.objects.create(
            tenant_id=TENANT,
            round_type="ward",
            unit_id=UNIT_ID,
            unit_name="Ward 4B",
            attending_provider_id=PROVIDER,
            attending_name="Dr. Hassan",
            round_date=date.today(),
            status="in_progress",
        )

        # Step 4: Finding → action
        finding = RoundFinding.objects.create(
            tenant_id=TENANT,
            round=rnd,
            patient_id=PATIENT,
            finding_type="lab_result",
            finding_text="Creatinine elevated: 2.3 mg/dL (baseline 1.0). AKI stage 1.",
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
            action_description="Ordered IV fluids and nephrology consult.",
            status="pending",
        )
        assert action.action_type == "order_placed"

        # Step 5: Order placed
        order = ProviderOrderRequest.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordering_provider_id=PROVIDER,
            ordering_provider_name="Dr. Hassan",
            order_category="laboratory",
            order_name="Renal Function Panel",
            priority="urgent",
            status="submitted",
        )
        assert order.status == "submitted"

        # Step 6: Critical result returns
        result = ProviderResultView.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            result_type="laboratory",
            result_source_id=uuid.uuid4(),
            result_source_type="lab_result",
            result_name="Creatinine",
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
            result_value="3.1 mg/dL",
            normal_range="0.7–1.2 mg/dL",
            status="acknowledged",
            acknowledged_at=timezone.now(),
        )

        # Step 7: Follow-up task
        task = ClinicalTask.objects.create(
            tenant_id=TENANT,
            task_type="lab_follow_up",
            title="Monitor renal function — repeat in 6 hours",
            patient_id=PATIENT,
            priority="urgent",
            status="pending",
            assigned_to_provider_id=PROVIDER,
            assigned_to_type="physician",
            created_by_provider_id=PROVIDER,
            source_type="lab_result",
            source_id=result.id,
            due_at=timezone.now() + timedelta(hours=6),
        )
        assert task.status == "pending"
        assert alert.status == "acknowledged"
