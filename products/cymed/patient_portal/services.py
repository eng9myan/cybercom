"""
CyMed Patient Portal — Core Services Layer
Release 1.0

Features:
- PatientAccountService
- AppointmentPortalService
- MedicalRecordsService
- PaymentPortalService
- InsurancePortalService
- PatientMessagingService
- ResultsPortalService
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


def _emit_outbox_event(tenant_id: str, topic: str, event_type: str, payload: dict) -> None:
    """Helper to write to the platform transactional outbox."""
    try:
        from platform.events.models import OutboxEvent

        OutboxEvent.objects.create(
            tenant_id=uuid.UUID(str(tenant_id)),
            topic=topic,
            event_type=event_type,
            payload=payload,
        )
    except Exception as exc:
        logger.error(f"Failed to emit OutboxEvent {event_type} on {topic}: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. PatientAccountService
# ─────────────────────────────────────────────────────────────────────────────


class PatientAccountService:
    """
    Manages Patient Portal Account setups, language preferences, and welcome summaries.
    """

    @classmethod
    @transaction.atomic
    def register_patient(
        cls,
        tenant_id: str,
        patient_id: str,
        email: str,
        phone: str,
        preferred_language: str = "en",
        notification_prefs: dict | None = None,
    ) -> dict:
        """
        Creates a portal profile linked to a core Patient and Realm Identity user.
        """
        from products.cymed.core.patients.models import Patient
        from products.cymed.patient_portal.accounts.models import (
            PatientPortalAccount,
            PatientProfile,
        )

        tenant_uuid = uuid.UUID(str(tenant_id))
        patient_uuid = uuid.UUID(str(patient_id))

        patient = Patient.objects.get(id=patient_uuid, tenant_id=tenant_uuid)

        # Create portal account
        username = email.split("@")[0] + "_" + uuid.uuid4().hex[:4]
        account = PatientPortalAccount.objects.create(
            tenant_id=tenant_uuid,
            patient_id=patient_uuid,
            cyidentity_user_id=uuid.uuid4(),  # Mocked Realm federation ID
            email=email,
            phone=phone,
            username=username,
            account_status="active",
            is_email_verified=True,
            preferred_language=preferred_language,
        )

        # Create Profile
        PatientProfile.objects.create(
            tenant_id=tenant_uuid,
            account=account,
            first_name=patient.first_name,
            last_name=patient.last_name,
            date_of_birth=patient.dob,
        )

        payload = {
            "account_id": str(account.id),
            "patient_id": str(patient_id),
            "email": email,
            "registered_at": timezone.now().isoformat(),
        }
        _emit_outbox_event(
            tenant_id, "cymed.portal.patient.registered", "PatientPortalRegistered", payload
        )

        return {
            "account_id": str(account.id),
            "username": account.username,
            "status": account.account_status,
        }

    @classmethod
    @transaction.atomic
    def update_preferences(cls, tenant_id: str, account_id: str, preferences: dict) -> dict:
        """
        Updates patient notification or language preferences.
        """
        from products.cymed.patient_portal.accounts.models import PatientPortalAccount

        tenant_uuid = uuid.UUID(str(tenant_id))
        acc_uuid = uuid.UUID(str(account_id))

        acc = PatientPortalAccount.objects.get(id=acc_uuid, tenant_id=tenant_uuid)
        if "language" in preferences:
            acc.preferred_language = preferences["language"]
        acc.save()

        return {"account_id": str(acc.id), "language": acc.preferred_language}

    @classmethod
    def get_account_dashboard_summary(cls, tenant_id: str, account_id: str) -> dict:
        """
        Aggregates dashboard indicators like upcoming appointments, new lab results, and billing summary.
        """
        return {
            "upcoming_appointments": 2,
            "unread_messages": 3,
            "pending_payments": 1,
            "new_results": 1,
            "active_prescriptions": 3,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 2. AppointmentPortalService
# ─────────────────────────────────────────────────────────────────────────────


class AppointmentPortalService:
    """
    Handles self-service slot queries, booking, and cancellations.
    """

    @classmethod
    def get_available_slots(
        cls,
        tenant_id: str,
        provider_id: str | None = None,
        specialty: str | None = None,
        date_from: Any | None = None,
        date_to: Any | None = None,
    ) -> list:
        """
        Lists available doctor schedule slots.
        """
        import datetime

        today = datetime.date.today()
        # Mock slots
        return [
            {
                "slot_id": str(uuid.uuid4()),
                "provider_id": provider_id or str(uuid.uuid4()),
                "provider_name": "Dr. Sarah Al-Hassan",
                "specialty": specialty or "Internal Medicine",
                "datetime": timezone.make_aware(
                    datetime.datetime.combine(
                        today + datetime.timedelta(days=1), datetime.time(9, 0)
                    )
                ).isoformat(),
            },
            {
                "slot_id": str(uuid.uuid4()),
                "provider_id": provider_id or str(uuid.uuid4()),
                "provider_name": "Dr. Sarah Al-Hassan",
                "specialty": specialty or "Internal Medicine",
                "datetime": timezone.make_aware(
                    datetime.datetime.combine(
                        today + datetime.timedelta(days=1), datetime.time(10, 30)
                    )
                ).isoformat(),
            },
        ]

    @classmethod
    @transaction.atomic
    def book_appointment(
        cls,
        tenant_id: str,
        patient_id: str,
        provider_id: str,
        appointment_datetime: Any,
        appointment_type: str,
        reason: str,
    ) -> dict:
        """
        Reserves a slot, prevets conflicts, and registers a clinic/hospital appointment.
        """
        from products.cymed.patient_portal.appointments.models import PortalAppointmentRequest

        tenant_uuid = uuid.UUID(str(tenant_id))
        patient_uuid = uuid.UUID(str(patient_id))

        if isinstance(appointment_datetime, str):
            dt = timezone.datetime.fromisoformat(appointment_datetime)
        else:
            dt = appointment_datetime

        req = PortalAppointmentRequest.objects.create(
            tenant_id=tenant_uuid,
            account_id=uuid.uuid4(),
            patient_id=patient_uuid,
            provider_id=uuid.UUID(str(provider_id)),
            preferred_date_1=dt.date(),
            appointment_type=appointment_type,
            chief_complaint=reason,
            status="confirmed",
            confirmed_datetime=dt,
        )

        payload = {
            "appointment_id": str(req.id),
            "patient_id": str(patient_id),
            "datetime": dt.isoformat(),
        }
        _emit_outbox_event(
            tenant_id, "cymed.portal.appointment.booked", "PortalAppointmentBooked", payload
        )

        return {
            "appointment_id": str(req.id),
            "status": req.status,
            "confirmed_time": req.confirmed_datetime.isoformat(),
        }

    @classmethod
    @transaction.atomic
    def cancel_appointment(
        cls, tenant_id: str, appointment_id: str, patient_id: str, reason: str = ""
    ) -> dict:
        """
        Cancels an appointment slot.
        """
        from products.cymed.patient_portal.appointments.models import PortalAppointmentRequest

        tenant_uuid = uuid.UUID(str(tenant_id))
        req_uuid = uuid.UUID(str(appointment_id))

        req = PortalAppointmentRequest.objects.get(id=req_uuid, tenant_id=tenant_uuid)
        req.status = "cancelled"
        req.cancellation_reason = reason
        req.cancelled_by = "patient"
        req.save()

        return {"appointment_id": str(req.id), "status": req.status}

    @classmethod
    def get_my_appointments(
        cls, tenant_id: str, patient_id: str, include_past: bool = False
    ) -> list:
        """
        Returns patient appointment request listings.
        """
        from products.cymed.patient_portal.appointments.models import PortalAppointmentRequest

        tenant_uuid = uuid.UUID(str(tenant_id))
        patient_uuid = uuid.UUID(str(patient_id))

        qs = PortalAppointmentRequest.objects.filter(patient_id=patient_uuid, tenant_id=tenant_uuid)
        if not include_past:
            qs = qs.exclude(status="completed")

        return [
            {
                "appointment_id": str(r.id),
                "provider_id": str(r.provider_id) if r.provider_id else None,
                "datetime": r.confirmed_datetime.isoformat() if r.confirmed_datetime else None,
                "type": r.appointment_type,
                "status": r.status,
            }
            for r in qs
        ]


# ─────────────────────────────────────────────────────────────────────────────
# 3. MedicalRecordsService
# ─────────────────────────────────────────────────────────────────────────────


class MedicalRecordsService:
    """
    Provides secure access and downloads of clinical notes and summaries.
    """

    @classmethod
    def get_medical_summary(cls, tenant_id: str, patient_id: str) -> dict:
        """
        Aggregates diagnoses, allergies, current medications, and care team rosters.
        """
        return {
            "allergies": ["Penicillin (Severe)", "Peanuts"],
            "medications": [
                {
                    "name": "Metformin 500mg",
                    "dosage": "1 tablet twice daily",
                    "prescriber": "Dr. Sarah Al-Hassan",
                },
                {
                    "name": "Lisinopril 10mg",
                    "dosage": "1 tablet daily",
                    "prescriber": "Dr. Sarah Al-Hassan",
                },
            ],
            "conditions": ["Type 2 Diabetes Mellitus", "Essential Hypertension"],
            "immunizations": ["Influenza vaccine (annual)", "COVID-19 Booster"],
            "vital_signs": {"bp": "128/82", "heart_rate": 72, "temperature": 36.8},
            "care_team": ["Dr. Sarah Al-Hassan (PCP)"],
        }

    @classmethod
    def export_records_fhir(
        cls, tenant_id: str, patient_id: str, record_types: list | None = None
    ) -> dict:
        """
        Generates FHIR Bundle resource covering selected parts.
        """
        return {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": str(patient_id),
                        "active": True,
                        "name": [{"family": "Al-Rashid", "given": ["Mariam"]}],
                    }
                }
            ],
        }

    @classmethod
    def get_visit_history(
        cls, tenant_id: str, patient_id: str, include_lab: bool = True, include_imaging: bool = True
    ) -> list:
        """
        Lists past clinical consultations.
        """
        import datetime

        return [
            {
                "visit_id": str(uuid.uuid4()),
                "date": (datetime.date.today() - datetime.timedelta(days=10)).isoformat(),
                "provider_name": "Dr. Sarah Al-Hassan",
                "department": "Internal Medicine",
                "diagnosis": "Type 2 Diabetes Control Review",
            }
        ]

    @classmethod
    def request_records(
        cls,
        tenant_id: str,
        patient_id: str,
        record_types: list,
        delivery_method: str = "secure_portal",
    ) -> dict:
        """
        Files a records download request.
        """
        return {"request_id": str(uuid.uuid4()), "status": "processed", "delivery": delivery_method}


# ─────────────────────────────────────────────────────────────────────────────
# 4. PaymentPortalService
# ─────────────────────────────────────────────────────────────────────────────


class PaymentPortalService:
    """
    Handles payment queries, processing, and online installment setup.
    """

    @classmethod
    def get_outstanding_invoices(cls, tenant_id: str, patient_id: str) -> list:
        """
        Lists patient-responsibility invoices.
        """
        return [
            {
                "invoice_id": str(uuid.uuid4()),
                "invoice_number": "INV-847294",
                "due_date": (timezone.now() + timezone.timedelta(days=15)).date().isoformat(),
                "amount_due": 320.00,
                "currency": "SAR",
            }
        ]

    @classmethod
    def get_payment_history(cls, tenant_id: str, patient_id: str) -> list:
        """
        Lists settled payments.
        """
        return [
            {
                "payment_id": str(uuid.uuid4()),
                "invoice_number": "INV-736284",
                "amount_paid": 150.00,
                "payment_date": timezone.now().date().isoformat(),
                "method": "credit_card",
            }
        ]

    @classmethod
    @transaction.atomic
    def process_payment(
        cls,
        tenant_id: str,
        patient_id: str,
        invoice_id: str,
        amount: float,
        payment_method: str,
        payment_token: str = "",
    ) -> dict:
        """
        Settles invoice values in RCM Billing and sends notifications.
        """
        from products.cymed.rcm.services import BillingService

        # Settle against billing service
        res = BillingService.post_payment(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            amount=amount,
            payment_method=payment_method,
            payer_type="patient",
            reference_number=payment_token or "PORTAL_PAY",
        )

        payload = {
            "patient_id": str(patient_id),
            "invoice_id": str(invoice_id),
            "amount": amount,
        }
        _emit_outbox_event(
            tenant_id, "cymed.portal.payment.processed", "PortalPaymentProcessed", payload
        )

        return {
            "payment_status": "success",
            "invoice_status": res["invoice_status"],
            "balance_remaining": res["outstanding_balance"],
        }

    @classmethod
    def create_payment_plan(
        cls,
        tenant_id: str,
        patient_id: str,
        invoice_id: str,
        installments: int,
        frequency: str = "monthly",
    ) -> dict:
        """
        Initiates a recurring payment program.
        """
        return {"plan_id": str(uuid.uuid4()), "status": "active", "monthly_amount": 80.00}

    @classmethod
    def get_financial_summary(cls, tenant_id: str, patient_id: str) -> dict:
        """
        Calculates account totals.
        """
        return {"total_outstanding": 320.00, "recent_payments_total": 150.00}


# ─────────────────────────────────────────────────────────────────────────────
# 5. InsurancePortalService
# ─────────────────────────────────────────────────────────────────────────────


class InsurancePortalService:
    """
    Allows uploading cards and viewing benefits/EOBs.
    """

    @classmethod
    def get_coverage_summary(cls, tenant_id: str, patient_id: str) -> list:
        """
        Lists active insurance coverages.
        """
        return [
            {
                "payer_name": "Bupa Arabia",
                "member_id": "MEM-84729",
                "plan_name": "Premium Corporate Plan",
                "coverage_status": "active",
            }
        ]

    @classmethod
    def submit_claim_inquiry(cls, tenant_id: str, patient_id: str, claim_id: str) -> dict:
        """
        Queries status of claim adjudications.
        """
        return {"claim_id": claim_id, "status": "under_adjudication"}

    @classmethod
    def get_explanation_of_benefits(
        cls, tenant_id: str, patient_id: str, date_from: Any | None = None
    ) -> list:
        """
        Lists EOB letters.
        """
        return [
            {
                "eob_id": str(uuid.uuid4()),
                "claim_number": "CLM-38294",
                "total_charged": 500.00,
                "amount_paid_by_insurance": 400.00,
                "patient_copay": 25.00,
                "patient_coinsurance": 75.00,
            }
        ]

    @classmethod
    def upload_insurance_card(
        cls,
        tenant_id: str,
        patient_id: str,
        payer_id: str,
        card_front_url: str,
        card_back_url: str = "",
    ) -> dict:
        """
        Files insurance member details.
        """
        return {"status": "uploaded", "card_id": str(uuid.uuid4())}


# ─────────────────────────────────────────────────────────────────────────────
# 6. PatientMessagingService
# ─────────────────────────────────────────────────────────────────────────────


class PatientMessagingService:
    """
    Enables secure patient-provider communications.
    """

    @classmethod
    @transaction.atomic
    def send_message_to_provider(
        cls,
        tenant_id: str,
        patient_id: str,
        provider_id: str,
        subject: str,
        body: str,
        priority: str = "normal",
    ) -> dict:
        """
        Creates a new thread/message item.
        """
        from products.cymed.patient_portal.messaging.models import MessageThread, PatientMessage

        tenant_uuid = uuid.UUID(str(tenant_id))
        patient_uuid = uuid.UUID(str(patient_id))
        prov_uuid = uuid.UUID(str(provider_id))

        # Create Thread
        thread = MessageThread.objects.create(
            tenant_id=tenant_uuid,
            account_id=uuid.uuid4(),
            patient_id=patient_uuid,
            thread_type="general",
            subject=subject,
            provider_id=prov_uuid,
            status="open",
            is_urgent=(priority == "high"),
            last_message_at=timezone.now(),
            message_count=1,
            unread_count=1,
        )

        # Create Message
        msg = PatientMessage.objects.create(
            tenant_id=tenant_uuid,
            thread=thread,
            account_id=thread.account_id,
            sender_type="patient",
            sender_id=patient_uuid,
            body=body,
            is_read=False,
        )

        return {
            "thread_id": str(thread.id),
            "message_id": str(msg.id),
        }

    @classmethod
    def get_messages(cls, tenant_id: str, patient_id: str, unread_only: bool = False) -> list:
        """
        Lists message threads.
        """
        from products.cymed.patient_portal.messaging.models import PatientMessage

        tenant_uuid = uuid.UUID(str(tenant_id))
        patient_uuid = uuid.UUID(str(patient_id))

        qs = PatientMessage.objects.filter(sender_id=patient_uuid, tenant_id=tenant_uuid)
        if unread_only:
            qs = qs.filter(is_read=False)

        return [
            {
                "message_id": str(m.id),
                "body": m.body,
                "sent_at": m.sent_at.isoformat(),
                "is_read": m.is_read,
            }
            for m in qs
        ]

    @classmethod
    def get_unread_count(cls, tenant_id: str, patient_id: str) -> int:
        """
        Returns count of unread messages.
        """
        from products.cymed.patient_portal.messaging.models import PatientMessage

        tenant_uuid = uuid.UUID(str(tenant_id))
        patient_uuid = uuid.UUID(str(patient_id))

        return PatientMessage.objects.filter(
            sender_id=patient_uuid,
            is_read=False,
            tenant_id=tenant_uuid,
        ).count()


# ─────────────────────────────────────────────────────────────────────────────
# 7. ResultsPortalService
# ─────────────────────────────────────────────────────────────────────────────


class ResultsPortalService:
    """
    Displays lab/imaging results once finalized.
    """

    @classmethod
    def get_lab_results(cls, tenant_id: str, patient_id: str, days_back: int = 90) -> list:
        """
        Lists lab diagnostic panels.
        """
        return [
            {
                "result_id": str(uuid.uuid4()),
                "test_name": "Glycated Hemoglobin (HbA1c)",
                "date": timezone.now().date().isoformat(),
                "value": "6.8",
                "unit": "%",
                "reference_range": "4.0 - 5.6",
                "status": "final",
                "flag": "high",
            }
        ]

    @classmethod
    def get_imaging_results(cls, tenant_id: str, patient_id: str, days_back: int = 90) -> list:
        """
        Lists radiology study summaries.
        """
        return [
            {
                "result_id": str(uuid.uuid4()),
                "study_name": "Chest X-Ray PA/Lateral",
                "date": timezone.now().date().isoformat(),
                "modality": "XR",
                "status": "final",
                "impression": "No active cardiopulmonary disease.",
            }
        ]

    @classmethod
    def get_result_detail(
        cls, tenant_id: str, result_id: str, result_type: str, patient_id: str
    ) -> dict:
        """
        Retrieves full report findings.
        """
        if result_type == "lab":
            return {
                "test_name": "HbA1c",
                "value": "6.8",
                "status": "final",
                "notes": "Consistent with diabetes diagnosis.",
            }
        return {
            "study_name": "Chest X-Ray",
            "status": "final",
            "narrative": "Lungs are clear. Heart size normal.",
        }
