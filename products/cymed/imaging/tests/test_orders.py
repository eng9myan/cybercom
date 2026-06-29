"""
Tests: CyMed Imaging — Orders, Procedures, Protocols
"""

import uuid

import pytest

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
PROVIDER = uuid.uuid4()


@pytest.mark.django_db
class TestImagingProtocol:
    def test_create_protocol(self):
        from products.cymed.imaging.orders.models import ImagingProtocol

        proto = ImagingProtocol.objects.create(
            tenant_id=TENANT,
            name="CT Chest Protocol",
            modality="ct",
            description="Standard chest CT",
            parameters={"kVp": 120, "mAs": "auto"},
        )
        assert proto.name == "CT Chest Protocol"
        assert proto.is_active is True

    def test_create_procedure(self):
        from products.cymed.imaging.orders.models import ImagingProcedure

        proc = ImagingProcedure.objects.create(
            tenant_id=TENANT,
            code="CT-CHEST",
            name="CT Chest",
            modality="ct",
            body_part="chest",
            snomed_code="399208008",
            loinc_code="24627-2",
            duration_minutes=15,
            contrast_required=False,
        )
        assert proc.code == "CT-CHEST"
        assert proc.is_active is True

    def test_procedure_with_protocol(self):
        from products.cymed.imaging.orders.models import ImagingProcedure, ImagingProtocol

        proto = ImagingProtocol.objects.create(tenant_id=TENANT, name="MRI Brain", modality="mri")
        proc = ImagingProcedure.objects.create(
            tenant_id=TENANT,
            code=f"MRI-BRAIN-{uuid.uuid4().hex[:4]}",
            name="MRI Brain",
            modality="mri",
            protocol=proto,
            contrast_required=True,
            duration_minutes=45,
        )
        assert proc.protocol == proto
        assert proc.contrast_required is True

    def test_create_imaging_order(self):
        from products.cymed.imaging.orders.models import ImagingOrder

        order = ImagingOrder.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordered_by=PROVIDER,
            order_number=f"IMG-{uuid.uuid4().hex[:8].upper()}",
            order_type="outpatient",
            priority="routine",
            clinical_indication="Persistent cough",
        )
        assert order.status == "pending"
        assert order.priority == "routine"

    def test_imaging_order_item(self):
        from products.cymed.imaging.orders.models import (
            ImagingOrder,
            ImagingOrderItem,
            ImagingProcedure,
        )

        proc = ImagingProcedure.objects.create(
            tenant_id=TENANT,
            code=f"XR-{uuid.uuid4().hex[:4]}",
            name="Chest X-Ray",
            modality="xray",
        )
        order = ImagingOrder.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordered_by=PROVIDER,
            order_number=f"IMG-{uuid.uuid4().hex[:8].upper()}",
        )
        item = ImagingOrderItem.objects.create(
            tenant_id=TENANT,
            order=order,
            procedure=proc,
            body_part="chest",
            laterality="none",
        )
        assert item.status == "pending"
        assert item.order == order

    def test_order_status_history(self):
        from products.cymed.imaging.orders.models import ImagingOrder, ImagingOrderStatusHistory

        order = ImagingOrder.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordered_by=PROVIDER,
            order_number=f"IMG-{uuid.uuid4().hex[:8].upper()}",
        )
        history = ImagingOrderStatusHistory.objects.create(
            tenant_id=TENANT,
            order=order,
            from_status="",
            to_status="pending",
            changed_by=PROVIDER,
        )
        assert history.to_status == "pending"

    def test_tenant_isolation(self):
        from products.cymed.imaging.orders.models import ImagingOrder

        other_tenant = uuid.uuid4()
        ImagingOrder.objects.create(
            tenant_id=other_tenant,
            patient_id=PATIENT,
            ordered_by=PROVIDER,
            order_number=f"IMG-OTHER-{uuid.uuid4().hex[:8]}",
        )
        ImagingOrder.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordered_by=PROVIDER,
            order_number=f"IMG-{uuid.uuid4().hex[:8]}",
        )
        assert ImagingOrder.objects.filter(tenant_id=TENANT).count() == 1
        assert ImagingOrder.objects.filter(tenant_id=other_tenant).count() == 1
