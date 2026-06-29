"""
Tests: CyMed Laboratory — Specimen Management
"""

import datetime
import uuid

import pytest

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
PROVIDER = uuid.uuid4()


@pytest.mark.django_db
class TestSpecimen:
    def test_create_specimen(self):
        from products.cymed.laboratory.specimens.models import Specimen, SpecimenStatus

        sp = Specimen.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            specimen_number="SP-001",
            barcode="BC-001",
            specimen_type="blood",
        )
        assert sp.status == SpecimenStatus.PENDING
        assert "SP-001" in str(sp)

    def test_specimen_collection(self):
        from products.cymed.laboratory.specimens.models import Specimen, SpecimenCollection

        sp = Specimen.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            specimen_number="SP-002",
            barcode="BC-002",
            specimen_type="serum",
        )
        now = datetime.datetime.now(tz=datetime.UTC)
        coll = SpecimenCollection.objects.create(
            tenant_id=TENANT,
            specimen=sp,
            collected_by=PROVIDER,
            collected_at=now,
            collection_site="Phlebotomy Bay A",
        )
        assert coll.specimen == sp

    def test_specimen_rejection(self):
        from products.cymed.laboratory.specimens.models import Specimen, SpecimenRejection

        sp = Specimen.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            specimen_number="SP-003",
            barcode="BC-003",
            specimen_type="blood",
        )
        rej = SpecimenRejection.objects.create(
            tenant_id=TENANT,
            specimen=sp,
            rejection_reason="hemolyzed",
            rejected_by=PROVIDER,
            action_taken="recollect",
        )
        assert rej.rejection_reason == "hemolyzed"

    def test_chain_of_custody(self):
        from products.cymed.laboratory.specimens.models import Specimen, SpecimenChainOfCustody

        sp = Specimen.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            specimen_number="SP-004",
            barcode="BC-004",
            specimen_type="urine",
        )
        now = datetime.datetime.now(tz=datetime.UTC)
        event = SpecimenChainOfCustody.objects.create(
            tenant_id=TENANT,
            specimen=sp,
            action="collected",
            performed_by=PROVIDER,
            location="Ward 3",
            action_timestamp=now,
        )
        assert event.action == "collected"

    def test_specimen_transport(self):
        from products.cymed.laboratory.specimens.models import Specimen, SpecimenTransport

        sp = Specimen.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            specimen_number="SP-005",
            barcode="BC-005",
            specimen_type="csf",
        )
        now = datetime.datetime.now(tz=datetime.UTC)
        t = SpecimenTransport.objects.create(
            tenant_id=TENANT,
            specimen=sp,
            from_location="ICU",
            to_location="Lab",
            dispatched_at=now,
            status="dispatched",
        )
        assert t.status == "dispatched"

    def test_specimen_container(self):
        from products.cymed.laboratory.specimens.models import Specimen, SpecimenContainer

        sp = Specimen.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            specimen_number="SP-006",
            barcode="BC-006",
            specimen_type="blood",
        )
        c = SpecimenContainer.objects.create(
            tenant_id=TENANT,
            specimen=sp,
            container_type="edta",
            barcode="CONT-001",
        )
        assert c.is_primary is True
