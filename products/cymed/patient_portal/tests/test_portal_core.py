"""
CyMed Patient Portal — Core Tests (Phase 3.6)
Covers: accounts, directory, family_accounts, consents,
        appointments, telemedicine, medical_records
Target coverage: 90%+
"""

import uuid
from datetime import date, timedelta

import pytest

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
ACCOUNT_USER = uuid.uuid4()
PHARMACIST = uuid.uuid4()
OTHER_TENANT = uuid.uuid4()


# ──────────────────────────────────────────────────
# ACCOUNTS TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestPatientPortalAccount:
    def test_create_account(self):
        from products.cymed.patient_portal.accounts.models import PatientPortalAccount

        acct = PatientPortalAccount.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            cyidentity_user_id=ACCOUNT_USER,
            email="patient@example.com",
            username="patient001",
            account_status="active",
        )
        assert acct.email == "patient@example.com"
        assert acct.account_status == "active"
        assert acct.is_email_verified is False

    def test_patient_profile(self):
        from products.cymed.patient_portal.accounts.models import (
            PatientPortalAccount,
            PatientProfile,
        )

        acct = PatientPortalAccount.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            cyidentity_user_id=uuid.uuid4(),
            email="p2@example.com",
            username="p2",
        )
        profile = PatientProfile.objects.create(
            tenant_id=TENANT,
            account=acct,
            first_name="Ali",
            last_name="Al-Nsour",
            date_of_birth=date(1985, 3, 15),
            gender="male",
            blood_group="O+",
        )
        assert profile.first_name == "Ali"
        assert profile.blood_group == "O+"

    def test_patient_preferences(self):
        from products.cymed.patient_portal.accounts.models import (
            PatientPortalAccount,
            PatientPreferences,
        )

        acct = PatientPortalAccount.objects.create(
            tenant_id=TENANT,
            patient_id=uuid.uuid4(),
            cyidentity_user_id=uuid.uuid4(),
            email="p3@example.com",
            username="p3",
        )
        prefs = PatientPreferences.objects.create(
            tenant_id=TENANT,
            account=acct,
            preferred_language="ar",
            sms_notifications=False,
            marketing_communications=False,
        )
        assert prefs.preferred_language == "ar"
        assert prefs.push_notifications is True
        assert prefs.sms_notifications is False

    def test_security_settings(self):
        from products.cymed.patient_portal.accounts.models import (
            PatientPortalAccount,
            PatientSecuritySettings,
        )

        acct = PatientPortalAccount.objects.create(
            tenant_id=TENANT,
            patient_id=uuid.uuid4(),
            cyidentity_user_id=uuid.uuid4(),
            email="p4@example.com",
            username="p4",
        )
        sec = PatientSecuritySettings.objects.create(
            tenant_id=TENANT,
            account=acct,
            mfa_enabled=True,
            mfa_method="totp",
            biometric_enabled=True,
        )
        assert sec.mfa_enabled is True
        assert sec.mfa_method == "totp"
        assert sec.failed_login_count == 0

    def test_patient_device(self):
        from products.cymed.patient_portal.accounts.models import (
            PatientDevice,
            PatientPortalAccount,
        )

        acct = PatientPortalAccount.objects.create(
            tenant_id=TENANT,
            patient_id=uuid.uuid4(),
            cyidentity_user_id=uuid.uuid4(),
            email="p5@example.com",
            username="p5",
        )
        device = PatientDevice.objects.create(
            tenant_id=TENANT,
            account=acct,
            device_name="iPhone 15",
            device_type="ios",
            device_token="apns-token-abc123",
            is_trusted=True,
        )
        assert device.device_type == "ios"
        assert device.is_trusted is True
        assert acct.devices.count() == 1

    def test_account_tenant_isolation(self):
        from products.cymed.patient_portal.accounts.models import PatientPortalAccount

        PatientPortalAccount.objects.create(
            tenant_id=TENANT,
            patient_id=uuid.uuid4(),
            cyidentity_user_id=uuid.uuid4(),
            email="iso1@t1.com",
            username="iso1",
        )
        PatientPortalAccount.objects.create(
            tenant_id=OTHER_TENANT,
            patient_id=uuid.uuid4(),
            cyidentity_user_id=uuid.uuid4(),
            email="iso2@t2.com",
            username="iso2",
        )
        assert PatientPortalAccount.objects.filter(tenant_id=TENANT).count() == 1
        assert PatientPortalAccount.objects.filter(tenant_id=OTHER_TENANT).count() == 1


# ──────────────────────────────────────────────────
# DIRECTORY TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestProviderDirectory:
    def test_create_hospital_listing(self):
        from products.cymed.patient_portal.directory.models import HospitalListing

        hospital = HospitalListing.objects.create(
            tenant_id=TENANT,
            hospital_id=uuid.uuid4(),
            name="City General Hospital",
            name_ar="مستشفى المدينة العام",
            slug="city-general-hospital",
            address="King Fahd Rd, Riyadh",
            city="Riyadh",
            country="SAU",
            bed_count=450,
            is_published=True,
            is_featured=True,
            accepts_insurance=True,
        )
        assert hospital.name == "City General Hospital"
        assert hospital.bed_count == 450
        assert hospital.is_featured is True

    def test_create_clinic_listing(self):
        from products.cymed.patient_portal.directory.models import ClinicListing

        clinic = ClinicListing.objects.create(
            tenant_id=TENANT,
            clinic_id=uuid.uuid4(),
            name="Al-Nour Cardiology Clinic",
            slug="alnour-cardiology",
            address="123 Medical St",
            city="Dubai",
            country="ARE",
            primary_specialty="cardiology",
            telemedicine_available=True,
        )
        assert clinic.primary_specialty == "cardiology"
        assert clinic.telemedicine_available is True

    def test_clinic_specialties(self):
        from products.cymed.patient_portal.directory.models import ClinicSpecialty

        specs = [
            ClinicSpecialty.objects.create(tenant_id=TENANT, code=code, name=name, display_order=i)
            for i, (code, name) in enumerate(
                [
                    ("cardiology", "Cardiology"),
                    ("dermatology", "Dermatology"),
                    ("pediatrics", "Pediatrics"),
                    ("orthopedics", "Orthopedics"),
                    ("neurology", "Neurology"),
                    ("ent", "ENT"),
                    ("ophthalmology", "Ophthalmology"),
                    ("internal_medicine", "Internal Medicine"),
                ]
            )
        ]
        assert len(specs) == 8
        assert ClinicSpecialty.objects.filter(tenant_id=TENANT).count() == 8

    def test_laboratory_listing(self):
        from products.cymed.patient_portal.directory.models import LaboratoryListing

        lab = LaboratoryListing.objects.create(
            tenant_id=TENANT,
            lab_id=uuid.uuid4(),
            name="Alpha Diagnostics",
            slug="alpha-diagnostics",
            address="456 Lab Ave",
            city="Cairo",
            country="EGY",
            home_collection=True,
            accreditations=["CAP", "ISO 15189"],
        )
        assert lab.home_collection is True
        assert "CAP" in lab.accreditations

    def test_imaging_center_listing(self):
        from products.cymed.patient_portal.directory.models import ImagingCenterListing

        center = ImagingCenterListing.objects.create(
            tenant_id=TENANT,
            center_id=uuid.uuid4(),
            name="Premier Radiology",
            slug="premier-radiology",
            address="789 Imaging Blvd",
            city="Amman",
            country="JOR",
            modalities=["MRI", "CT", "X-Ray", "Ultrasound"],
        )
        assert "MRI" in center.modalities
        assert len(center.modalities) == 4

    def test_pharmacy_listing(self):
        from products.cymed.patient_portal.directory.models import PharmacyListing

        pharmacy = PharmacyListing.objects.create(
            tenant_id=TENANT,
            pharmacy_id=uuid.uuid4(),
            name="24/7 Health Pharmacy",
            slug="health-pharmacy-main",
            address="Main Street 1",
            city="Beirut",
            country="LBN",
            is_24_hours=True,
            home_delivery=True,
        )
        assert pharmacy.is_24_hours is True
        assert pharmacy.home_delivery is True

    def test_provider_review(self):
        from products.cymed.patient_portal.directory.models import ProviderReview

        review = ProviderReview.objects.create(
            tenant_id=TENANT,
            reviewer_account_id=uuid.uuid4(),
            provider_type="hospital",
            provider_listing_id=uuid.uuid4(),
            rating=5,
            title="Excellent care",
            review_text="Highly professional staff.",
            is_verified_visit=True,
            is_published=False,
        )
        assert review.rating == 5
        assert review.is_published is False


# ──────────────────────────────────────────────────
# FAMILY ACCOUNTS TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestFamilyAccounts:
    def test_create_family_group(self):
        from products.cymed.patient_portal.family_accounts.models import FamilyGroup

        group = FamilyGroup.objects.create(
            tenant_id=TENANT,
            owner_account_id=uuid.uuid4(),
            group_name="Al-Nsour Family",
        )
        assert group.group_name == "Al-Nsour Family"
        assert group.is_active is True

    def test_add_family_members(self):
        from products.cymed.patient_portal.family_accounts.models import FamilyGroup, FamilyMember

        owner = uuid.uuid4()
        group = FamilyGroup.objects.create(
            tenant_id=TENANT,
            owner_account_id=owner,
            group_name="Test Family",
        )
        child = FamilyMember.objects.create(
            tenant_id=TENANT,
            group=group,
            patient_id=uuid.uuid4(),
            first_name="Youssef",
            last_name="Ali",
            date_of_birth=date(2015, 6, 10),
            relationship="child",
            is_minor=True,
            added_by=owner,
        )
        assert child.is_minor is True
        assert child.relationship == "child"
        assert group.members.count() == 1

    def test_family_access_permission(self):
        from products.cymed.patient_portal.family_accounts.models import FamilyAccessPermission

        grantor = uuid.uuid4()
        grantee = uuid.uuid4()
        perm = FamilyAccessPermission.objects.create(
            tenant_id=TENANT,
            grantor_account_id=grantor,
            grantee_account_id=grantee,
            patient_id=uuid.uuid4(),
            access_level="view_only",
            permissions=["lab_results", "appointments"],
            is_active=True,
        )
        assert perm.access_level == "view_only"
        assert "lab_results" in perm.permissions
        assert perm.is_active is True

    def test_dependent_profile(self):
        from products.cymed.patient_portal.family_accounts.models import (
            DependentProfile,
            FamilyGroup,
            FamilyMember,
        )

        owner = uuid.uuid4()
        group = FamilyGroup.objects.create(tenant_id=TENANT, owner_account_id=owner)
        member = FamilyMember.objects.create(
            tenant_id=TENANT,
            group=group,
            patient_id=uuid.uuid4(),
            first_name="Sara",
            last_name="Ali",
            relationship="child",
            is_minor=True,
            added_by=owner,
        )
        dep = DependentProfile.objects.create(
            tenant_id=TENANT,
            member=member,
            guardian_account_id=owner,
            school_name="Al-Noor Elementary",
            immunization_up_to_date=True,
        )
        assert dep.immunization_up_to_date is True


# ──────────────────────────────────────────────────
# CONSENTS TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestConsents:
    def test_create_consent_type(self):
        from products.cymed.patient_portal.consents.models import PortalConsentType

        ct = PortalConsentType.objects.create(
            tenant_id=TENANT,
            code="TELE_CONSENT",
            name="Telemedicine Consent",
            description="Consent to receive telemedicine services.",
            consent_category="telemedicine",
            is_mandatory=True,
            version="2.0",
        )
        assert ct.code == "TELE_CONSENT"
        assert ct.is_mandatory is True

    def test_grant_consent(self):
        from django.utils import timezone

        from products.cymed.patient_portal.consents.models import (
            PortalConsentRecord,
            PortalConsentType,
        )

        ct = PortalConsentType.objects.create(
            tenant_id=TENANT,
            code="TREATMENT_CONSENT",
            name="Treatment Consent",
            description="General treatment consent.",
            consent_category="treatment",
            is_mandatory=True,
        )
        record = PortalConsentRecord.objects.create(
            tenant_id=TENANT,
            account_id=uuid.uuid4(),
            patient_id=PATIENT,
            consent_type=ct,
            consent_status="granted",
            granted_at=timezone.now(),
            version_consented="1.0",
            channel="portal",
        )
        assert record.consent_status == "granted"
        assert record.channel == "portal"

    def test_consent_request(self):
        from products.cymed.patient_portal.consents.models import ConsentRequest, PortalConsentType

        ct = PortalConsentType.objects.create(
            tenant_id=TENANT,
            code="RESEARCH_CONSENT",
            name="Research Consent",
            description="Data research consent.",
            consent_category="research",
            is_mandatory=False,
        )
        req = ConsentRequest.objects.create(
            tenant_id=TENANT,
            account_id=uuid.uuid4(),
            patient_id=PATIENT,
            consent_type=ct,
            requested_by=uuid.uuid4(),
            requester_name="Dr. Smith",
            request_reason="Clinical trial enrollment",
            status="pending",
        )
        assert req.status == "pending"

    def test_consent_history(self):
        from django.utils import timezone

        from products.cymed.patient_portal.consents.models import (
            ConsentHistory,
            PortalConsentRecord,
            PortalConsentType,
        )

        ct = PortalConsentType.objects.create(
            tenant_id=TENANT,
            code="DATA_CONSENT",
            name="Data Sharing Consent",
            description="Data sharing.",
            consent_category="data_sharing",
        )
        record = PortalConsentRecord.objects.create(
            tenant_id=TENANT,
            account_id=uuid.uuid4(),
            patient_id=PATIENT,
            consent_type=ct,
            consent_status="granted",
            granted_at=timezone.now(),
        )
        h = ConsentHistory.objects.create(
            tenant_id=TENANT,
            consent_record=record,
            action="granted",
            previous_status="pending",
            new_status="granted",
            changed_by=uuid.uuid4(),
        )
        assert h.action == "granted"


# ──────────────────────────────────────────────────
# APPOINTMENTS TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestPortalAppointments:
    def test_create_appointment_request(self):
        from products.cymed.patient_portal.appointments.models import PortalAppointmentRequest

        req = PortalAppointmentRequest.objects.create(
            tenant_id=TENANT,
            account_id=uuid.uuid4(),
            patient_id=PATIENT,
            provider_type="clinic",
            provider_name="Al-Nour Cardiology",
            specialty="cardiology",
            preferred_date_1=date.today() + timedelta(days=3),
            appointment_type="consultation",
            chief_complaint="Chest pain and shortness of breath",
            status="pending",
        )
        assert req.status == "pending"
        assert req.appointment_type == "consultation"

    def test_appointment_reminder(self):
        from django.utils import timezone

        from products.cymed.patient_portal.appointments.models import (
            AppointmentReminder,
            PortalAppointmentRequest,
        )

        req = PortalAppointmentRequest.objects.create(
            tenant_id=TENANT,
            account_id=uuid.uuid4(),
            patient_id=PATIENT,
            provider_type="hospital",
            status="confirmed",
        )
        reminder = AppointmentReminder.objects.create(
            tenant_id=TENANT,
            appointment_request=req,
            reminder_type="push",
            scheduled_at=timezone.now() + timedelta(hours=1),
            reminder_hours_before=24,
            status="pending",
        )
        assert reminder.reminder_type == "push"
        assert reminder.status == "pending"

    def test_waitlist_entry(self):
        from products.cymed.patient_portal.appointments.models import WaitlistEntry

        entry = WaitlistEntry.objects.create(
            tenant_id=TENANT,
            account_id=uuid.uuid4(),
            patient_id=PATIENT,
            provider_id=uuid.uuid4(),
            specialty="orthopedics",
            waitlist_type="next_available",
            priority="routine",
            status="waiting",
        )
        assert entry.status == "waiting"
        assert entry.priority == "routine"

    def test_appointment_rating(self):
        from products.cymed.patient_portal.appointments.models import (
            AppointmentRating,
            PortalAppointmentRequest,
        )

        req = PortalAppointmentRequest.objects.create(
            tenant_id=TENANT,
            account_id=uuid.uuid4(),
            patient_id=PATIENT,
            status="completed",
        )
        rating = AppointmentRating.objects.create(
            tenant_id=TENANT,
            appointment_request=req,
            account_id=uuid.uuid4(),
            overall_rating=5,
            wait_time_rating=4,
            staff_rating=5,
            physician_rating=5,
            comment="Excellent experience!",
            would_recommend=True,
        )
        assert rating.overall_rating == 5
        assert rating.would_recommend is True


# ──────────────────────────────────────────────────
# TELEMEDICINE TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestTelemedicine:
    def test_create_telemedicine_session(self):
        from django.utils import timezone

        from products.cymed.patient_portal.telemedicine.models import TelemedicineSession

        session = TelemedicineSession.objects.create(
            tenant_id=TENANT,
            account_id=uuid.uuid4(),
            patient_id=PATIENT,
            provider_id=uuid.uuid4(),
            provider_name="Dr. Khaled Al-Ahmad",
            session_type="video",
            status="scheduled",
            scheduled_at=timezone.now() + timedelta(hours=2),
            meeting_url="https://meet.cymed.health/session/abc123",
        )
        assert session.session_type == "video"
        assert session.status == "scheduled"

    def test_telemedicine_document(self):
        from django.utils import timezone

        from products.cymed.patient_portal.telemedicine.models import (
            TelemedicineDocument,
            TelemedicineSession,
        )

        session = TelemedicineSession.objects.create(
            tenant_id=TENANT,
            account_id=uuid.uuid4(),
            patient_id=PATIENT,
            provider_id=uuid.uuid4(),
            provider_name="Dr. Test",
            session_type="video",
            status="in_progress",
            scheduled_at=timezone.now(),
        )
        doc = TelemedicineDocument.objects.create(
            tenant_id=TENANT,
            session=session,
            document_type="lab_result",
            file_name="blood_test.pdf",
            file_url="https://cydata.example.com/docs/blood_test.pdf",
            file_size_bytes=512000,
            file_type="application/pdf",
            uploaded_by="patient",
        )
        assert doc.document_type == "lab_result"
        assert session.documents.count() == 1

    def test_telemedicine_chat(self):
        from django.utils import timezone

        from products.cymed.patient_portal.telemedicine.models import (
            TelemedicineChat,
            TelemedicineSession,
        )

        session = TelemedicineSession.objects.create(
            tenant_id=TENANT,
            account_id=uuid.uuid4(),
            patient_id=PATIENT,
            provider_id=uuid.uuid4(),
            provider_name="Dr. Test",
            session_type="chat",
            status="in_progress",
            scheduled_at=timezone.now(),
        )
        msg = TelemedicineChat.objects.create(
            tenant_id=TENANT,
            session=session,
            sender_type="patient",
            sender_id=PATIENT,
            message="Hello, I've been having headaches for 3 days.",
        )
        assert msg.sender_type == "patient"
        assert msg.read_at is None

    def test_telemedicine_rating(self):
        from django.utils import timezone

        from products.cymed.patient_portal.telemedicine.models import (
            TelemedicineRating,
            TelemedicineSession,
        )

        session = TelemedicineSession.objects.create(
            tenant_id=TENANT,
            account_id=uuid.uuid4(),
            patient_id=PATIENT,
            provider_id=uuid.uuid4(),
            provider_name="Dr. Test",
            session_type="video",
            status="completed",
            scheduled_at=timezone.now(),
        )
        rating = TelemedicineRating.objects.create(
            tenant_id=TENANT,
            session=session,
            account_id=uuid.uuid4(),
            overall_rating=4,
            video_quality_rating=5,
            audio_quality_rating=4,
            provider_rating=5,
            would_use_again=True,
        )
        assert rating.overall_rating == 4
        assert rating.would_use_again is True


# ──────────────────────────────────────────────────
# MEDICAL RECORDS TESTS
# ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestMedicalRecords:
    def test_record_access_log(self):
        from products.cymed.patient_portal.medical_records.models import MedicalRecordAccess

        acc = MedicalRecordAccess.objects.create(
            tenant_id=TENANT,
            account_id=uuid.uuid4(),
            patient_id=PATIENT,
            record_type="diagnosis",
            record_id=uuid.uuid4(),
            access_type="view",
            access_context="portal",
        )
        assert acc.record_type == "diagnosis"
        assert acc.access_type == "view"

    def test_shared_record(self):
        from django.utils import timezone

        from products.cymed.patient_portal.medical_records.models import SharedRecord

        share = SharedRecord.objects.create(
            tenant_id=TENANT,
            account_id=uuid.uuid4(),
            patient_id=PATIENT,
            record_type="lab_result",
            record_id=uuid.uuid4(),
            record_title="CBC Report 2026-06-20",
            shared_with_type="provider",
            shared_with_name="Dr. Hassan",
            shared_with_email="hassan@clinic.com",
            share_token="tok_abc123xyz",
            valid_until=timezone.now() + timedelta(days=7),
        )
        assert share.is_revoked is False
        assert share.access_count == 0

    def test_download_history(self):
        from products.cymed.patient_portal.medical_records.models import RecordDownloadHistory

        dl = RecordDownloadHistory.objects.create(
            tenant_id=TENANT,
            account_id=uuid.uuid4(),
            patient_id=PATIENT,
            record_type="imaging",
            record_id=uuid.uuid4(),
            record_title="Chest X-Ray Report",
            download_format="pdf",
        )
        assert dl.download_format == "pdf"

    def test_patient_document_upload(self):
        from products.cymed.patient_portal.medical_records.models import PatientDocument

        doc = PatientDocument.objects.create(
            tenant_id=TENANT,
            account_id=uuid.uuid4(),
            patient_id=PATIENT,
            document_type="report",
            title="Annual Physical Exam 2025",
            file_name="physical_2025.pdf",
            file_url="https://cydata.example.com/docs/physical_2025.pdf",
            file_size_bytes=1024000,
            file_type="application/pdf",
            document_date=date(2025, 12, 15),
            source="uploaded_by_patient",
        )
        assert doc.document_type == "report"
        assert doc.is_shared is False
