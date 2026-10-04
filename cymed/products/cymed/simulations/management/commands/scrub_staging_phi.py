"""
Scrubs PHI/PII in THIS database so it's safe to expose as a staging
environment (reachable by more people than production). Part of Phase 4
(Odoo.sh-equivalent hosting)'s staging-clone-from-prod flow:
infrastructure/scripts/clone-staging-from-prod.sh runs this, via
`manage.py scrub_staging_phi --yes-this-is-staging`, against the freshly
pg_restore'd staging database only — never production.

Why a management command and not a raw SQL script: several PHI columns are
`EncryptedText` with a `blind_index=True` companion `<field>_bidx` column
(a deterministic HMAC enabling exact-match lookup without decrypting). A
raw `UPDATE ... SET first_name = NULL` would (a) violate the column's
NOT NULL constraint and (b) leave the OLD blind index sitting in
`first_name_bidx`, letting someone confirm "does a patient named X exist"
in staging even after the plaintext is gone. Going through the real model
field's `.save()` re-runs `EncryptedText.pre_save()`, which re-encrypts
AND re-derives the blind index correctly — the only way to scrub correctly
without hand-rolling the same crypto here.

NOT an exhaustive PHI inventory. Covers the patient-identity core
(Patient + its identifiers/contacts/addresses), secure messaging bodies,
and the core clinical narrative fields (condition/observation/flag text).
A full compliance-grade scrub would need to walk every `EncryptedText`
column across the whole product (lab results, imaging reports, nursing
notes, dispensing counseling notes, ...) — flagged as a follow-up, not
done here.
"""
from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = (
        "Irreversibly scrubs PHI/PII in this database for safe staging use. "
        "Refuses to run without --yes-this-is-staging."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes-this-is-staging", action="store_true", dest="confirmed",
            help="Required. Confirms this database is a staging/non-production copy.",
        )
        parser.add_argument(
            "--batch-size", type=int, default=500,
            help="Rows fetched per batch while iterating (default 500).",
        )

    def handle(self, *args, **options):
        if not options["confirmed"]:
            raise CommandError(
                "Refusing to run without --yes-this-is-staging. This command rewrites "
                "PHI in place and cannot be undone — never run it against production."
            )
        batch_size = options["batch_size"]

        with transaction.atomic():
            patients = self._scrub_patients(batch_size)
            threads = self._scrub_messaging(batch_size)
            clinical = self._scrub_clinical(batch_size)

        self.stdout.write(self.style.SUCCESS(
            f"Scrubbed {patients} patients, {threads} message threads, {clinical} clinical records."
        ))

    def _scrub_patients(self, batch_size: int) -> int:
        from products.cymed.core.patients.models import Patient, PatientContact, PatientAddress, PatientIdentifier

        count = 0
        for patient in Patient.objects.all().iterator(chunk_size=batch_size):
            patient.first_name = "Staging"
            patient.last_name = f"Patient{count:08d}"
            patient.mrn = f"STAGING-{patient.id.hex[:12].upper()}"
            patient.national_id = ""
            patient.passport_number = ""
            patient.save()
            count += 1

        for contact in PatientContact.objects.all().iterator(chunk_size=batch_size):
            contact.telecom_value = "redacted@staging.invalid" if contact.telecom_system == "email" else "0000000000"
            contact.save()

        for addr in PatientAddress.objects.all().iterator(chunk_size=batch_size):
            addr.line1 = "123 Staging St"
            addr.line2 = ""
            addr.postal_code = "00000"
            addr.save()

        # PatientIdentifier.value is a plain (unencrypted) CharField, no blind
        # index to maintain — a bulk update is correct and fine here.
        PatientIdentifier.objects.update(value="REDACTED")

        return count

    def _scrub_messaging(self, batch_size: int) -> int:
        from products.cymed.core.messaging.models import MessageThread, Message

        count = 0
        for thread in MessageThread.objects.all().iterator(chunk_size=batch_size):
            thread.subject = "Staging message"
            thread.save()
            count += 1

        for message in Message.objects.all().iterator(chunk_size=batch_size):
            message.body = "[content scrubbed for staging]"
            message.save()

        return count

    def _scrub_clinical(self, batch_size: int) -> int:
        from products.cymed.core.clinical.models import Condition, Observation, ClinicalFlag

        count = 0
        for condition in Condition.objects.all().iterator(chunk_size=batch_size):
            condition.display = "Scrubbed condition"
            condition.save()
            count += 1

        for obs in Observation.objects.exclude(value_string="").iterator(chunk_size=batch_size):
            obs.value_string = "[scrubbed]"
            obs.save()

        for flag in ClinicalFlag.objects.all().iterator(chunk_size=batch_size):
            flag.flag_text = "[scrubbed]"
            flag.save()

        return count
