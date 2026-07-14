import random

from django.db import transaction
from django.utils import timezone

from platform.events.models import OutboxEvent
from products.cymed.core.patients.models import Patient, PatientMergeHistory


class PatientService:
    @classmethod
    def generate_mrn(cls) -> str:
        """Generates a unique Medical Record Number (MRN)."""
        year = timezone.now().year
        rand_num = random.randint(10000, 99999)
        return f"MRN-{year}-{rand_num}"

    @classmethod
    def detect_duplicates(
        cls,
        first_name: str,
        last_name: str,
        dob,
        tenant_id: str,
        national_id: str = None,
        passport_number: str = None,
    ):
        """
        Fuzzy duplicate detection for patients in the same tenant.
        Finds patients with matching National ID, Passport, or matching Name + DOB.
        """
        # 1. Exact match on National ID or Passport
        if national_id:
            qs = Patient.objects.filter(
                tenant_id=tenant_id, national_id=national_id, is_active=True
            )
            if qs.exists():
                return qs
        if passport_number:
            qs = Patient.objects.filter(
                tenant_id=tenant_id, passport_number=passport_number, is_active=True
            )
            if qs.exists():
                return qs

        # 2. Fuzzy name match + DOB match
        # Checks if first name starts similarly and DOB matches
        name_qs = Patient.objects.filter(
            tenant_id=tenant_id,
            dob=dob,
            is_active=True,
            first_name__icontains=first_name[:3],
            last_name__icontains=last_name[:3],
        )
        return name_qs

    @classmethod
    def merge_patients(
        cls, source_id: str, target_id: str, tenant_id: str, merged_by: str
    ) -> PatientMergeHistory:
        """
        Merges source patient into target patient.
        Disables source patient, references target patient, and logs history + event.
        """
        with transaction.atomic():
            source = Patient.objects.get(id=source_id, tenant_id=tenant_id)
            target = Patient.objects.get(id=target_id, tenant_id=tenant_id)

            if source == target:
                raise ValueError("Cannot merge a patient into themselves.")

            source.merged_into = target
            source.is_active = False
            source.save()

            history = PatientMergeHistory.objects.create(
                tenant_id=tenant_id,
                merged_patient=source,
                target_patient=target,
                merged_by=merged_by,
                merged_at=timezone.now(),
            )

            # Publish event
            OutboxEvent.objects.create(
                tenant_id=tenant_id,
                topic="cymed.patient.events",
                event_type="cymed.patient.merged",
                payload={
                    "source_patient_id": str(source.id),
                    "target_patient_id": str(target.id),
                    "merged_by": merged_by,
                    "merged_at": history.merged_at.isoformat(),
                },
            )

            return history

    @classmethod
    def unmerge_patients(
        cls, history_id: str, tenant_id: str, unmerged_by: str
    ) -> PatientMergeHistory:
        """
        Restores a merged patient and clears the merge reference.
        """
        with transaction.atomic():
            history = PatientMergeHistory.objects.get(id=history_id, tenant_id=tenant_id)
            source = history.merged_patient

            source.merged_into = None
            source.is_active = True
            source.save()

            history.unmerged_at = timezone.now()
            history.unmerged_by = unmerged_by
            history.save()

            # Publish event
            OutboxEvent.objects.create(
                tenant_id=tenant_id,
                topic="cymed.patient.events",
                event_type="cymed.patient.unmerged",
                payload={
                    "source_patient_id": str(source.id),
                    "target_patient_id": str(history.target_patient.id),
                    "unmerged_by": unmerged_by,
                    "unmerged_at": history.unmerged_at.isoformat(),
                },
            )

            return history
