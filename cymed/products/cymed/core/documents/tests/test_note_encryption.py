"""Clinical free-text is encrypted per-tenant at rest."""

import uuid

import pytest

from platform.common.fields import MASK
from platform.common.tenant_context import tenant_context
from products.cymed.core.documents.models import ClinicalDocument, ProgressNote, SOAPNote
from products.cymed.core.patients.models import Patient


@pytest.mark.django_db
def test_note_text_round_trips_in_context_and_masks_without():
    tid = uuid.uuid4()
    with tenant_context(tid):
        patient = Patient.objects.create(
            tenant_id=tid, first_name="A", last_name="B", dob="1990-01-01", mrn="MRN-NE-1"
        )
        doc = ClinicalDocument.objects.create(
            tenant_id=tid, patient=patient, title="SOAP", document_type="soap",
            content="Chief complaint: chest pain radiating to left arm.",
        )
        soap = SOAPNote.objects.create(
            tenant_id=tid, clinical_document=doc,
            subjective="Pain since morning", objective="BP 150/95",
            assessment="Rule out ACS", plan="ECG, troponin, aspirin",
        )
        ProgressNote.objects.create(
            tenant_id=tid, clinical_document=doc, narrative="Patient stable overnight.",
        )

        doc.refresh_from_db()
        soap.refresh_from_db()
        assert doc.content.startswith("Chief complaint")
        assert soap.plan == "ECG, troponin, aspirin"

    # no tenant context -> masked, never the plaintext
    assert ClinicalDocument.objects.get(id=doc.id).content == MASK
    assert SOAPNote.objects.get(id=soap.id).subjective == MASK


@pytest.mark.django_db
def test_blank_note_fields_are_fine():
    tid = uuid.uuid4()
    with tenant_context(tid):
        patient = Patient.objects.create(
            tenant_id=tid, first_name="C", last_name="D", dob="1990-01-01", mrn="MRN-NE-2"
        )
        doc = ClinicalDocument.objects.create(
            tenant_id=tid, patient=patient, title="Empty", document_type="progress",
        )
        doc.refresh_from_db()
        assert doc.content in ("", None)
