"""
Tests: CyMed Imaging — Scheduling and Modality Worklist
"""

import datetime
import uuid

import pytest

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
PROVIDER = uuid.uuid4()
TECH = uuid.uuid4()
RAD = uuid.uuid4()


def make_modality(tenant_id, code=None, modality_type="ct"):
    from products.cymed.imaging.modality_worklist.models import Modality

    return Modality.objects.create(
        tenant_id=tenant_id,
        code=code or f"MOD-{uuid.uuid4().hex[:4]}",
        name="Modality",
        modality_type=modality_type,
        ae_title="CYMED_CT1",
    )


def make_order_item(tenant_id):
    from products.cymed.imaging.orders.models import (
        ImagingOrder,
        ImagingOrderItem,
        ImagingProcedure,
    )

    proc = ImagingProcedure.objects.create(
        tenant_id=tenant_id,
        code=f"PROC-{uuid.uuid4().hex[:4]}",
        name="Test Proc",
        modality="ct",
    )
    order = ImagingOrder.objects.create(
        tenant_id=tenant_id,
        patient_id=PATIENT,
        ordered_by=PROVIDER,
        order_number=f"IMG-{uuid.uuid4().hex[:8].upper()}",
    )
    return ImagingOrderItem.objects.create(tenant_id=tenant_id, order=order, procedure=proc)


@pytest.mark.django_db
class TestModality:
    def test_create_modality(self):
        from products.cymed.imaging.modality_worklist.models import Modality

        mod = Modality.objects.create(
            tenant_id=TENANT,
            code="CT-001",
            name="Siemens SOMATOM",
            modality_type="ct",
            manufacturer="Siemens",
            ae_title="CT001",
            ip_address="192.168.1.100",
        )
        assert mod.is_active is True
        assert "CT-001" in str(mod)

    def test_worklist_creation(self):
        from products.cymed.imaging.modality_worklist.models import ModalityWorklist

        mod = make_modality(TENANT, code="MRI-001", modality_type="mri")
        wl = ModalityWorklist.objects.create(
            tenant_id=TENANT,
            modality=mod,
            worklist_date=datetime.date.today(),
            created_by=PROVIDER,
        )
        assert wl.status == "open"
        assert "MRI-001" in str(wl)

    def test_worklist_entry(self):
        from products.cymed.imaging.modality_worklist.models import ModalityWorklist, WorklistEntry

        mod = make_modality(TENANT)
        wl = ModalityWorklist.objects.create(
            tenant_id=TENANT,
            modality=mod,
            worklist_date=datetime.date.today(),
            created_by=PROVIDER,
        )
        item = make_order_item(TENANT)
        entry = WorklistEntry.objects.create(
            tenant_id=TENANT,
            worklist=wl,
            order_item=item,
            patient_id=PATIENT,
            priority_rank=1,
        )
        assert entry.status == "pending"
        assert entry.images_acquired == 0

    def test_study_queue(self):
        from products.cymed.imaging.modality_worklist.models import StudyQueue

        item = make_order_item(TENANT)
        queue = StudyQueue.objects.create(
            tenant_id=TENANT,
            order_item=item,
            queue_type="reading",
            position=1,
        )
        assert queue.status == "queued"


@pytest.mark.django_db
class TestScheduling:
    def test_imaging_room(self):
        from products.cymed.imaging.scheduling.models import ImagingRoom

        room = ImagingRoom.objects.create(
            tenant_id=TENANT,
            code="CT-ROOM-1",
            name="CT Suite 1",
            modality_type="ct",
            building="A",
            floor="2",
        )
        assert room.is_active is True

    def test_imaging_appointment(self):
        from products.cymed.imaging.scheduling.models import ImagingAppointment, ImagingRoom

        mod = make_modality(TENANT)
        room = ImagingRoom.objects.create(
            tenant_id=TENANT,
            code=f"ROOM-{uuid.uuid4().hex[:4]}",
            name="Room 1",
            modality_type="ct",
        )
        item = make_order_item(TENANT)
        now = datetime.datetime.now(tz=datetime.UTC)
        appt = ImagingAppointment.objects.create(
            tenant_id=TENANT,
            order_item=item,
            patient_id=PATIENT,
            modality=mod,
            room=room,
            scheduled_start=now,
            scheduled_end=now + datetime.timedelta(minutes=30),
            duration_minutes=30,
            radiologist_id=RAD,
            technologist_id=TECH,
        )
        assert appt.status == "scheduled"
        assert appt.duration_minutes == 30

    def test_modality_schedule(self):
        from products.cymed.imaging.scheduling.models import ModalitySchedule

        mod = make_modality(TENANT)
        sched = ModalitySchedule.objects.create(
            tenant_id=TENANT,
            modality=mod,
            schedule_date=datetime.date.today(),
            start_time=datetime.time(8, 0),
            end_time=datetime.time(16, 0),
            available_slots=16,
        )
        assert sched.available_slots == 16
        assert sched.is_blocked is False

    def test_radiologist_schedule(self):
        from products.cymed.imaging.scheduling.models import RadiologistSchedule

        sched = RadiologistSchedule.objects.create(
            tenant_id=TENANT,
            radiologist_id=RAD,
            schedule_date=datetime.date.today(),
            start_time=datetime.time(8, 0),
            end_time=datetime.time(16, 0),
            modality_types=["ct", "mri"],
            subspecialty="neuroradiology",
            is_on_call=False,
        )
        assert sched.subspecialty == "neuroradiology"
        assert "ct" in sched.modality_types
