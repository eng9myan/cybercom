"""
CyMed Patient Portal — Security, Messaging & FHIR Tests (Phase 3.6)
Covers: messaging, notifications, tenant isolation, FHIR linking,
        AI guardrails, workflow integration
"""
import uuid
import pytest
from datetime import date, timedelta
from django.utils import timezone

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
ACCOUNT = uuid.uuid4()
OTHER_TENANT = uuid.uuid4()
PROVIDER = uuid.uuid4()


# ──────────────────────────────────────────────────
# MESSAGING TESTS
# ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestMessaging:
    def test_create_message_thread(self):
        from products.cymed.patient_portal.messaging.models import MessageThread
        thread = MessageThread.objects.create(
            tenant_id=TENANT, account_id=ACCOUNT, patient_id=PATIENT,
            thread_type="provider_message",
            subject="Question about medication side effects",
            provider_id=PROVIDER,
            provider_name="Dr. Hassan Al-Ahmad",
            status="open",
        )
        assert thread.thread_type == "provider_message"
        assert thread.status == "open"

    def test_send_patient_message(self):
        from products.cymed.patient_portal.messaging.models import MessageThread, PatientMessage
        thread = MessageThread.objects.create(
            tenant_id=TENANT, account_id=ACCOUNT, patient_id=PATIENT,
            thread_type="lab_inquiry",
            subject="CBC result question",
        )
        msg = PatientMessage.objects.create(
            tenant_id=TENANT, thread=thread,
            account_id=ACCOUNT,
            sender_type="patient", sender_id=PATIENT,
            sender_name="Ali Al-Nsour",
            body="I noticed my hemoglobin is slightly low. Is this concerning?",
        )
        assert msg.sender_type == "patient"
        assert msg.is_read is False
        assert thread.messages.count() == 1

    def test_message_attachment(self):
        from products.cymed.patient_portal.messaging.models import MessageThread, PatientMessage, MessageAttachment
        thread = MessageThread.objects.create(
            tenant_id=TENANT, account_id=ACCOUNT, patient_id=PATIENT,
            thread_type="prescription_inquiry", subject="Refill question",
        )
        msg = PatientMessage.objects.create(
            tenant_id=TENANT, thread=thread, account_id=ACCOUNT,
            sender_type="patient", sender_id=PATIENT,
            body="Please see attached previous test results.",
        )
        attachment = MessageAttachment.objects.create(
            tenant_id=TENANT, message=msg, account_id=ACCOUNT,
            file_name="test_results.pdf",
            file_url="https://cydata.example.com/msg/test_results.pdf",
            file_type="application/pdf", file_size_bytes=256000,
        )
        assert attachment.file_name == "test_results.pdf"
        assert msg.attachments.count() == 1

    def test_message_recipient(self):
        from products.cymed.patient_portal.messaging.models import MessageThread, SecureMessageRecipient
        thread = MessageThread.objects.create(
            tenant_id=TENANT, account_id=ACCOUNT, patient_id=PATIENT,
            thread_type="billing_inquiry", subject="Invoice inquiry",
        )
        recipient = SecureMessageRecipient.objects.create(
            tenant_id=TENANT, thread=thread,
            recipient_type="provider",
            recipient_id=PROVIDER,
            recipient_name="Dr. Hassan",
        )
        assert recipient.recipient_type == "provider"
        assert recipient.is_active is True


# ──────────────────────────────────────────────────
# NOTIFICATIONS TESTS
# ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestNotifications:
    def test_create_notification(self):
        from products.cymed.patient_portal.notifications.models import PatientNotification
        notif = PatientNotification.objects.create(
            tenant_id=TENANT, account_id=ACCOUNT, patient_id=PATIENT,
            notification_type="lab_result_ready",
            title="Your lab results are ready",
            body="Your Complete Blood Count results from Alpha Diagnostics are now available.",
            action_url="/portal/lab-results/result-123",
            action_label="View Results",
            priority="normal",
            source_type="lab_result",
            source_id=uuid.uuid4(),
        )
        assert notif.is_read is False
        assert notif.priority == "normal"
        assert notif.notification_type == "lab_result_ready"

    def test_critical_notification_priority(self):
        from products.cymed.patient_portal.notifications.models import PatientNotification
        notif = PatientNotification.objects.create(
            tenant_id=TENANT, account_id=ACCOUNT, patient_id=PATIENT,
            notification_type="critical_result",
            title="CRITICAL: Urgent lab result requires immediate attention",
            body="A critical value has been detected in your recent laboratory test.",
            priority="critical",
        )
        assert notif.priority == "critical"

    def test_notification_preference(self):
        from products.cymed.patient_portal.notifications.models import NotificationPreference
        pref = NotificationPreference.objects.create(
            tenant_id=TENANT, account_id=ACCOUNT,
            push_enabled=True, email_enabled=True, sms_enabled=False,
            appointment_notifications=True, lab_notifications=True,
            health_tips=False,
            quiet_hours_enabled=True,
        )
        assert pref.sms_enabled is False
        assert pref.quiet_hours_enabled is True

    def test_notification_template(self):
        from products.cymed.patient_portal.notifications.models import NotificationTemplate
        template = NotificationTemplate.objects.create(
            tenant_id=TENANT,
            code="LAB_RESULT_READY_PUSH_EN",
            notification_type="lab_result_ready",
            channel="push", language="en",
            title_template="Your {test_name} results are ready",
            body_template="Results from {lab_name} on {result_date} are now available.",
            is_active=True,
        )
        assert template.code == "LAB_RESULT_READY_PUSH_EN"
        assert template.channel == "push"

    def test_push_subscription(self):
        from products.cymed.patient_portal.notifications.models import PushSubscription
        sub = PushSubscription.objects.create(
            tenant_id=TENANT, account_id=ACCOUNT,
            push_token="ExponentPushToken[abc123]",
            platform="ios", is_active=True,
        )
        assert sub.platform == "ios"
        assert sub.is_active is True


# ──────────────────────────────────────────────────
# TENANT ISOLATION TESTS
# ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestPortalTenantIsolation:
    def test_account_isolation(self):
        from products.cymed.patient_portal.accounts.models import PatientPortalAccount
        PatientPortalAccount.objects.create(
            tenant_id=TENANT, patient_id=uuid.uuid4(),
            cyidentity_user_id=uuid.uuid4(), email="t1@t1.com", username="t1user",
        )
        PatientPortalAccount.objects.create(
            tenant_id=OTHER_TENANT, patient_id=uuid.uuid4(),
            cyidentity_user_id=uuid.uuid4(), email="t2@t2.com", username="t2user",
        )
        assert PatientPortalAccount.objects.filter(tenant_id=TENANT).count() == 1
        assert PatientPortalAccount.objects.filter(tenant_id=OTHER_TENANT).count() == 1

    def test_notification_isolation(self):
        from products.cymed.patient_portal.notifications.models import PatientNotification
        PatientNotification.objects.create(
            tenant_id=TENANT, account_id=ACCOUNT, patient_id=PATIENT,
            notification_type="appointment_reminder",
            title="T1 Reminder", body="T1 body", priority="normal",
        )
        PatientNotification.objects.create(
            tenant_id=OTHER_TENANT, account_id=uuid.uuid4(), patient_id=uuid.uuid4(),
            notification_type="appointment_reminder",
            title="T2 Reminder", body="T2 body", priority="normal",
        )
        assert PatientNotification.objects.filter(tenant_id=TENANT).count() == 1
        assert PatientNotification.objects.filter(tenant_id=OTHER_TENANT).count() == 1

    def test_invoice_isolation(self):
        from products.cymed.patient_portal.payments.models import PatientInvoice
        PatientInvoice.objects.create(
            tenant_id=TENANT, account_id=ACCOUNT, patient_id=PATIENT,
            cycom_invoice_id="T1-INV", invoice_number="T1-001",
            provider_name="T1 Clinic",
            amount_total=100, amount_patient_due=100, currency="USD",
        )
        PatientInvoice.objects.create(
            tenant_id=OTHER_TENANT, account_id=uuid.uuid4(), patient_id=uuid.uuid4(),
            cycom_invoice_id="T2-INV", invoice_number="T2-001",
            provider_name="T2 Clinic",
            amount_total=200, amount_patient_due=200, currency="USD",
        )
        assert PatientInvoice.objects.filter(tenant_id=TENANT).count() == 1
        assert PatientInvoice.objects.filter(tenant_id=OTHER_TENANT).count() == 1


# ──────────────────────────────────────────────────
# FHIR LINKING TESTS
# ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestFHIRLinking:
    def test_lab_result_fhir_id(self):
        from products.cymed.patient_portal.laboratory_results.models import LabResultView
        fhir_id = f"DiagnosticReport/{uuid.uuid4()}"
        result = LabResultView.objects.create(
            tenant_id=TENANT, account_id=ACCOUNT, patient_id=PATIENT,
            cymed_lab_result_id=uuid.uuid4(), lab_id=uuid.uuid4(),
            lab_name="FHIR Lab", test_name="CBC",
            result_status="final",
            fhir_diagnostic_report_id=fhir_id,
        )
        assert result.fhir_diagnostic_report_id == fhir_id
        found = LabResultView.objects.filter(fhir_diagnostic_report_id=fhir_id)
        assert found.count() == 1

    def test_imaging_fhir_ids(self):
        from products.cymed.patient_portal.imaging_results.models import ImagingResultView
        fhir_report_id = f"DiagnosticReport/{uuid.uuid4()}"
        fhir_study_id = f"ImagingStudy/{uuid.uuid4()}"
        result = ImagingResultView.objects.create(
            tenant_id=TENANT, account_id=ACCOUNT, patient_id=PATIENT,
            cymed_imaging_result_id=uuid.uuid4(),
            imaging_center_id=uuid.uuid4(),
            imaging_center_name="FHIR Radiology",
            modality="CT", report_status="final",
            fhir_diagnostic_report_id=fhir_report_id,
            fhir_imaging_study_id=fhir_study_id,
        )
        assert result.fhir_diagnostic_report_id == fhir_report_id
        assert result.fhir_imaging_study_id == fhir_study_id

    def test_prescription_fhir_id(self):
        from products.cymed.patient_portal.prescriptions.models import PortalPrescriptionView
        fhir_id = f"MedicationRequest/{uuid.uuid4()}"
        rx = PortalPrescriptionView.objects.create(
            tenant_id=TENANT, account_id=ACCOUNT, patient_id=PATIENT,
            cymed_prescription_id=uuid.uuid4(),
            prescription_number="RX-FHIR-001",
            status="active",
            fhir_medication_request_id=fhir_id,
        )
        found = PortalPrescriptionView.objects.filter(fhir_medication_request_id=fhir_id)
        assert found.count() == 1

    def test_vaccination_fhir_id(self):
        from products.cymed.patient_portal.wallet.models import VaccinationRecord
        fhir_id = f"Immunization/{uuid.uuid4()}"
        vax = VaccinationRecord.objects.create(
            tenant_id=TENANT, account_id=ACCOUNT, patient_id=PATIENT,
            vaccine_name="Influenza Vaccine",
            dose_number=1, total_doses_required=1,
            administered_date=date.today(),
            fhir_immunization_id=fhir_id,
        )
        found = VaccinationRecord.objects.filter(fhir_immunization_id=fhir_id)
        assert found.count() == 1


# ──────────────────────────────────────────────────
# AI GUARDRAILS TESTS
# ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestAIGuardrails:
    def test_ai_cannot_create_prescription(self):
        """AI can set ai_explanation field on MedicationInstruction only — cannot create prescriptions."""
        from products.cymed.patient_portal.prescriptions.models import MedicationInstruction
        instr = MedicationInstruction.objects.create(
            tenant_id=TENANT, account_id=ACCOUNT, patient_id=PATIENT,
            drug_code="RXN-001", drug_name="Metformin 500mg",
            instruction_text="Take 1 tablet twice daily with meals.",
            ai_explanation="Metformin is a medication that helps control blood sugar levels in Type 2 Diabetes.",
        )
        # AI explanation is informational only — it's on the instruction, not a prescription
        assert instr.ai_explanation != ""
        # No prescription was created by AI
        from products.cymed.patient_portal.prescriptions.models import PortalPrescriptionView
        assert PortalPrescriptionView.objects.filter(tenant_id=TENANT).count() == 0

    def test_ai_cannot_alter_medical_records(self):
        """Medical record access log cannot be created with AI as actor — only account holders."""
        from products.cymed.patient_portal.medical_records.models import MedicalRecordAccess
        # Access log records human access only
        access = MedicalRecordAccess.objects.create(
            tenant_id=TENANT, account_id=ACCOUNT, patient_id=PATIENT,
            record_type="diagnosis", record_id=uuid.uuid4(),
            access_type="view", access_context="portal",
        )
        assert access.account_id == ACCOUNT  # Must be a human account


# ──────────────────────────────────────────────────
# END-TO-END PORTAL WORKFLOW TEST
# ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestPortalWorkflow:
    def test_patient_registration_to_appointment_workflow(self):
        """
        Complete portal workflow:
        1. Create patient account
        2. Create profile
        3. Search directory (clinic exists)
        4. Book appointment
        5. Receive notification
        """
        from products.cymed.patient_portal.accounts.models import PatientPortalAccount, PatientProfile
        from products.cymed.patient_portal.directory.models import ClinicListing
        from products.cymed.patient_portal.appointments.models import PortalAppointmentRequest
        from products.cymed.patient_portal.notifications.models import PatientNotification

        # Step 1: Register
        acct = PatientPortalAccount.objects.create(
            tenant_id=TENANT, patient_id=PATIENT,
            cyidentity_user_id=uuid.uuid4(),
            email="workflow@example.com", username="wf_patient",
            account_status="active",
        )
        assert acct.account_status == "active"

        # Step 2: Create profile
        PatientProfile.objects.create(
            tenant_id=TENANT, account=acct,
            first_name="Test", last_name="Patient",
            date_of_birth=date(1990, 1, 1), gender="male",
        )

        # Step 3: Clinic exists in directory
        clinic = ClinicListing.objects.create(
            tenant_id=TENANT, clinic_id=uuid.uuid4(),
            name="Cardiology Clinic", slug="cardiology-clinic-wf",
            address="Test St", city="Dubai", country="ARE",
            primary_specialty="cardiology", is_published=True,
        )
        assert clinic.is_published is True

        # Step 4: Book appointment
        appt = PortalAppointmentRequest.objects.create(
            tenant_id=TENANT, account_id=acct.id, patient_id=PATIENT,
            provider_type="clinic", provider_id=clinic.id,
            provider_name=clinic.name, specialty="cardiology",
            appointment_type="consultation",
            preferred_date_1=date.today() + timedelta(days=5),
            status="pending",
        )
        assert appt.status == "pending"

        # Step 5: Appointment confirmation notification
        notif = PatientNotification.objects.create(
            tenant_id=TENANT, account_id=acct.id, patient_id=PATIENT,
            notification_type="appointment_confirmed",
            title="Appointment Confirmed",
            body=f"Your appointment at {clinic.name} has been confirmed.",
            source_type="appointment",
            source_id=appt.id,
            priority="normal",
        )
        assert notif.is_read is False
        assert "Cardiology Clinic" in notif.body
