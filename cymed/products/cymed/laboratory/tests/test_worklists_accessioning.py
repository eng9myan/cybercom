"""
Tests: CyMed Laboratory — Worklists, Analyzers, Accessioning
"""

import datetime
import uuid

import pytest

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
PROVIDER = uuid.uuid4()


@pytest.mark.django_db
class TestAnalyzer:
    def test_create_analyzer(self):
        from products.cymed.laboratory.worklists.models import Analyzer

        a = Analyzer.objects.create(
            tenant_id=TENANT,
            code="CHEM-001",
            name="Cobas c702",
            manufacturer="Roche",
            model_number="c702",
            analyzer_type="chemistry",
            department="chemistry",
        )
        assert a.is_active is True
        assert "CHEM-001" in str(a)

    def test_analyzer_interface(self):
        from products.cymed.laboratory.orders.models import LabTest
        from products.cymed.laboratory.worklists.models import Analyzer, AnalyzerInterface

        analyzer = Analyzer.objects.create(
            tenant_id=TENANT,
            code="CHEM-002",
            name="Analyzer 2",
            analyzer_type="chemistry",
            department="chemistry",
        )
        test = LabTest.objects.create(
            tenant_id=TENANT, code=f"GLU-{uuid.uuid4().hex[:4]}", name="Glucose"
        )
        iface = AnalyzerInterface.objects.create(
            tenant_id=TENANT,
            analyzer=analyzer,
            test=test,
            instrument_test_code="GLU",
            is_primary=True,
        )
        assert iface.instrument_test_code == "GLU"

    def test_analyzer_message(self):
        from products.cymed.laboratory.worklists.models import Analyzer, AnalyzerMessage

        analyzer = Analyzer.objects.create(
            tenant_id=TENANT,
            code="HEMA-001",
            name="XN-9000",
            analyzer_type="hematology",
            department="hematology",
        )
        msg = AnalyzerMessage.objects.create(
            tenant_id=TENANT,
            analyzer=analyzer,
            direction="inbound",
            message_type="ORU",
            raw_message="H|\\^&|||XN-9000|...",
        )
        assert msg.status == "received"


@pytest.mark.django_db
class TestWorklist:
    def test_create_worklist(self):
        from products.cymed.laboratory.worklists.models import LabWorklist

        wl = LabWorklist.objects.create(
            tenant_id=TENANT,
            name="Morning Chemistry",
            department="chemistry",
            worklist_date=datetime.date.today(),
            created_by=PROVIDER,
        )
        assert wl.status == "open"
        assert "Morning Chemistry" in str(wl)

    def test_worklist_item(self):
        from products.cymed.laboratory.orders.models import LabOrder, LabOrderItem, LabTest
        from products.cymed.laboratory.worklists.models import LabWorklist, WorklistItem

        test = LabTest.objects.create(
            tenant_id=TENANT, code=f"ALT-{uuid.uuid4().hex[:4]}", name="ALT"
        )
        order = LabOrder.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordered_by=PROVIDER,
            order_number=f"ORD-{uuid.uuid4().hex[:8]}",
        )
        item = LabOrderItem.objects.create(tenant_id=TENANT, order=order, test=test)
        wl = LabWorklist.objects.create(
            tenant_id=TENANT,
            name="Test WL",
            department="chemistry",
            worklist_date=datetime.date.today(),
            created_by=PROVIDER,
        )
        wi = WorklistItem.objects.create(
            tenant_id=TENANT,
            worklist=wl,
            order_item=item,
            sequence=1,
        )
        assert wi.status == "pending"

    def test_technologist_assignment(self):
        from products.cymed.laboratory.worklists.models import LabWorklist, TechnologistAssignment

        wl = LabWorklist.objects.create(
            tenant_id=TENANT,
            name="Afternoon WL",
            department="hematology",
            worklist_date=datetime.date.today(),
            created_by=PROVIDER,
        )
        assign = TechnologistAssignment.objects.create(
            tenant_id=TENANT,
            worklist=wl,
            technologist_id=PROVIDER,
            assigned_by=PROVIDER,
            items_target=50,
        )
        assert assign.status == "assigned"


@pytest.mark.django_db
class TestAccessioning:
    def test_accession_number_sequence(self):
        from products.cymed.laboratory.accessioning.models import AccessionNumberSequence

        seq = AccessionNumberSequence.objects.create(
            tenant_id=TENANT,
            site_code="HQ",
            year=2026,
            prefix="ACC",
            last_sequence=0,
        )
        number = seq.next_number()
        assert "ACC-HQ-2026-" in number
        assert number.endswith("000001")

    def test_accession_creation(self):
        from products.cymed.laboratory.accessioning.models import Accession
        from products.cymed.laboratory.specimens.models import Specimen

        sp = Specimen.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            specimen_number=f"SP-{uuid.uuid4().hex[:6]}",
            barcode=f"BC-{uuid.uuid4().hex[:6]}",
            specimen_type="blood",
        )
        acc = Accession.objects.create(
            tenant_id=TENANT,
            specimen=sp,
            accession_number="ACC-HQ-2026-000001",
            site_code="HQ",
            accessioned_by=PROVIDER,
        )
        assert acc.status == "active"
        assert str(acc) == "ACC-HQ-2026-000001"

    def test_accession_batch(self):
        from products.cymed.laboratory.accessioning.models import AccessionBatch

        batch = AccessionBatch.objects.create(
            tenant_id=TENANT,
            batch_number="BATCH-001",
            site_code="HQ",
            created_by=PROVIDER,
        )
        assert batch.is_open is True
