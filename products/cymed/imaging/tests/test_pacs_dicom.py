"""
Tests: CyMed Imaging — PACS Gateway and DICOM Registry
"""
import uuid
import pytest
import datetime

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
PROVIDER = uuid.uuid4()


def make_order_item(tenant_id):
    from products.cymed.imaging.orders.models import ImagingOrder, ImagingOrderItem, ImagingProcedure
    proc = ImagingProcedure.objects.create(
        tenant_id=tenant_id, code=f"PROC-{uuid.uuid4().hex[:4]}", name="CT Head", modality="ct",
    )
    order = ImagingOrder.objects.create(
        tenant_id=tenant_id, patient_id=PATIENT, ordered_by=PROVIDER,
        order_number=f"IMG-{uuid.uuid4().hex[:8].upper()}",
    )
    return ImagingOrderItem.objects.create(tenant_id=tenant_id, order=order, procedure=proc)


def make_pacs_node(tenant_id, code=None):
    from products.cymed.imaging.pacs_gateway.models import PACSNode
    return PACSNode.objects.create(
        tenant_id=tenant_id, code=code or f"PACS-{uuid.uuid4().hex[:4]}",
        name="Primary PACS", ae_title="PACS01",
        host="192.168.10.50", port=11112,
        protocol="dicom", is_primary=True,
    )


@pytest.mark.django_db
class TestPACSGateway:
    def test_create_pacs_node(self):
        from products.cymed.imaging.pacs_gateway.models import PACSNode
        node = PACSNode.objects.create(
            tenant_id=TENANT, code="PACS-001", name="Sectra PACS",
            ae_title="SECTRA01", host="10.0.0.50", port=11112,
            protocol="dicomweb",
            wado_rs_url="https://pacs.hospital.com/wado-rs",
            qido_rs_url="https://pacs.hospital.com/qido-rs",
            stow_rs_url="https://pacs.hospital.com/stow-rs",
            vendor="Sectra", tls_enabled=True,
        )
        assert node.is_active is True
        assert node.tls_enabled is True

    def test_pacs_query(self):
        from products.cymed.imaging.pacs_gateway.models import PACSNode, PACSQuery
        node = make_pacs_node(TENANT)
        query = PACSQuery.objects.create(
            tenant_id=TENANT, pacs_node=node,
            query_type="find", query_level="study",
            query_params={"PatientID": "12345", "StudyDate": "20260620"},
        )
        assert query.status == "pending"
        assert query.results_count == 0

    def test_study_route(self):
        from products.cymed.imaging.pacs_gateway.models import PACSNode, StudyRoute
        source = make_pacs_node(TENANT, code=f"SRC-{uuid.uuid4().hex[:4]}")
        dest = make_pacs_node(TENANT, code=f"DST-{uuid.uuid4().hex[:4]}")
        item = make_order_item(TENANT)
        route = StudyRoute.objects.create(
            tenant_id=TENANT, order_item=item,
            source_pacs=source, destination_pacs=dest,
            route_type="forward",
            study_instance_uid="1.2.840.10008.5.1.4.1.1.2.1234567890",
        )
        assert route.status == "pending"
        assert route.route_type == "forward"

    def test_pacs_event(self):
        from products.cymed.imaging.pacs_gateway.models import PACSNode, PACSEvent
        node = make_pacs_node(TENANT)
        event = PACSEvent.objects.create(
            tenant_id=TENANT, pacs_node=node,
            event_type="study_received",
            study_instance_uid="1.2.3.4.5.6789",
            details={"series_count": 3, "instance_count": 120},
        )
        assert event.acknowledged is False
        assert event.event_type == "study_received"


@pytest.mark.django_db
class TestDICOMRegistry:
    def make_pacs(self):
        return make_pacs_node(TENANT)

    def test_dicom_study(self):
        from products.cymed.imaging.dicom_registry.models import DICOMStudy
        pacs = self.make_pacs()
        study = DICOMStudy.objects.create(
            tenant_id=TENANT, patient_id=PATIENT,
            pacs_node=pacs,
            study_instance_uid=f"1.2.840.{uuid.uuid4().hex}",
            accession_number="ACC-2026-000001",
            modality="ct",
            study_date=datetime.date.today(),
            study_description="CT Chest Without Contrast",
            series_count=3, instance_count=120,
        )
        assert study.archive_status == "online"
        assert study.series_count == 3

    def test_dicom_series(self):
        from products.cymed.imaging.dicom_registry.models import DICOMStudy, DICOMSeries
        pacs = self.make_pacs()
        study = DICOMStudy.objects.create(
            tenant_id=TENANT, patient_id=PATIENT, pacs_node=pacs,
            study_instance_uid=f"1.2.840.{uuid.uuid4().hex}",
            modality="ct",
        )
        series = DICOMSeries.objects.create(
            tenant_id=TENANT, study=study,
            series_instance_uid=f"1.2.840.{uuid.uuid4().hex}.1",
            series_number=1,
            series_description="Axial",
            modality="ct", body_part="chest",
            instance_count=40,
            slice_thickness=__import__("decimal").Decimal("1.25"),
        )
        assert series.instance_count == 40

    def test_dicom_instance(self):
        from products.cymed.imaging.dicom_registry.models import DICOMStudy, DICOMSeries, DICOMInstance
        pacs = self.make_pacs()
        study = DICOMStudy.objects.create(
            tenant_id=TENANT, patient_id=PATIENT, pacs_node=pacs,
            study_instance_uid=f"1.2.840.{uuid.uuid4().hex}",
            modality="ct",
        )
        series = DICOMSeries.objects.create(
            tenant_id=TENANT, study=study,
            series_instance_uid=f"1.2.840.{uuid.uuid4().hex}.1",
        )
        inst = DICOMInstance.objects.create(
            tenant_id=TENANT, series=series,
            sop_instance_uid=f"1.2.840.{uuid.uuid4().hex}.1.1",
            sop_class_uid="1.2.840.10008.5.1.4.1.1.2",
            instance_number=1, rows=512, columns=512, bits_allocated=16,
        )
        assert inst.rows == 512

    def test_study_archive(self):
        from products.cymed.imaging.dicom_registry.models import DICOMStudy, StudyArchive
        pacs = self.make_pacs()
        study = DICOMStudy.objects.create(
            tenant_id=TENANT, patient_id=PATIENT, pacs_node=pacs,
            study_instance_uid=f"1.2.840.{uuid.uuid4().hex}",
            modality="mri", storage_size_mb=450,
        )
        archive = StudyArchive.objects.create(
            tenant_id=TENANT, study=study,
            archive_tier="hot", retention_years=10,
            compressed=True, compression_type="JPEG2000",
        )
        assert archive.archive_tier == "hot"
        assert archive.retention_years == 10
