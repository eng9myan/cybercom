"""
Tests: CyMed Imaging — Teleradiology and Quality
"""

import datetime
import uuid
from decimal import Decimal

import pytest

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
PROVIDER = uuid.uuid4()
RAD = uuid.uuid4()
RAD2 = uuid.uuid4()


def make_order_item(tenant_id):
    from products.cymed.imaging.orders.models import (
        ImagingOrder,
        ImagingOrderItem,
        ImagingProcedure,
    )

    proc = ImagingProcedure.objects.create(
        tenant_id=tenant_id,
        code=f"PROC-{uuid.uuid4().hex[:4]}",
        name="MRI Brain",
        modality="mri",
    )
    order = ImagingOrder.objects.create(
        tenant_id=tenant_id,
        patient_id=PATIENT,
        ordered_by=PROVIDER,
        order_number=f"IMG-{uuid.uuid4().hex[:8].upper()}",
    )
    return ImagingOrderItem.objects.create(tenant_id=tenant_id, order=order, procedure=proc)


def make_report(tenant_id):
    from products.cymed.imaging.radiology_reporting.models import RadiologyReport

    item = make_order_item(tenant_id)
    return RadiologyReport.objects.create(
        tenant_id=tenant_id,
        order_item=item,
        patient_id=PATIENT,
        radiologist_id=RAD,
        findings="Normal MRI brain",
        impression="No acute intracranial abnormality",
    )


def make_modality(tenant_id):
    from products.cymed.imaging.modality_worklist.models import Modality

    return Modality.objects.create(
        tenant_id=tenant_id,
        code=f"MOD-{uuid.uuid4().hex[:4]}",
        name="CT Scanner",
        modality_type="ct",
    )


@pytest.mark.django_db
class TestTeleradiology:
    def test_reading_queue(self):
        from products.cymed.imaging.teleradiology.models import ReadingQueue

        queue = ReadingQueue.objects.create(
            tenant_id=TENANT,
            name="Neuroradiology Queue",
            queue_type="subspecialty",
            subspecialty="neuroradiology",
            max_turnaround_hours=12,
        )
        assert queue.is_active is True
        assert queue.queue_type == "subspecialty"

    def test_teleradiology_case(self):
        from products.cymed.imaging.teleradiology.models import ReadingQueue, TeleradiologyCase

        queue = ReadingQueue.objects.create(
            tenant_id=TENANT,
            name="Urgent Queue",
            queue_type="urgent",
            max_turnaround_hours=1,
        )
        item = make_order_item(TENANT)
        case = TeleradiologyCase.objects.create(
            tenant_id=TENANT,
            order_item=item,
            reading_queue=queue,
            case_type="primary",
            originating_facility="Al-Noor Hospital",
            target_turnaround_hours=6,
            priority="stat",
        )
        assert case.status == "pending"
        assert case.priority == "stat"

    def test_reading_assignment(self):
        from products.cymed.imaging.teleradiology.models import ReadingAssignment, TeleradiologyCase

        item = make_order_item(TENANT)
        case = TeleradiologyCase.objects.create(
            tenant_id=TENANT,
            order_item=item,
            case_type="primary",
        )
        assignment = ReadingAssignment.objects.create(
            tenant_id=TENANT,
            teleradiology_case=case,
            radiologist_id=RAD,
            assigned_by=PROVIDER,
            subspecialty="neuroradiology",
        )
        assert assignment.status == "assigned"

    def test_second_opinion(self):
        from products.cymed.imaging.teleradiology.models import SecondOpinion

        report = make_report(TENANT)
        opinion = SecondOpinion.objects.create(
            tenant_id=TENANT,
            original_report=report,
            requested_by=PROVIDER,
            reason="Unexpected finding requiring expert consultation",
            clinical_question="Is this a glioma or metastasis?",
        )
        assert opinion.status == "pending"
        assert opinion.concurs_with_original is None

    def test_second_opinion_with_discrepancy(self):
        from products.cymed.imaging.teleradiology.models import SecondOpinion

        report = make_report(TENANT)
        opinion = SecondOpinion.objects.create(
            tenant_id=TENANT,
            original_report=report,
            requested_by=PROVIDER,
            reason="Review",
            second_opinion_radiologist_id=RAD2,
            status="completed",
            opinion_text="Finding is consistent with metastatic disease, not primary glioma.",
            concurs_with_original=False,
            discrepancy_level="major",
        )
        assert opinion.concurs_with_original is False
        assert opinion.discrepancy_level == "major"


@pytest.mark.django_db
class TestQuality:
    def test_quality_audit(self):
        from products.cymed.imaging.quality.models import QualityAudit

        report = make_report(TENANT)
        audit = QualityAudit.objects.create(
            tenant_id=TENANT,
            report=report,
            auditor_id=RAD2,
            audit_type="peer_review",
            score=4,
            feedback="Well-structured report.",
            discrepancy_level="none",
        )
        assert audit.score == 4
        assert audit.action_required is False

    def test_quality_audit_discrepancy(self):
        from products.cymed.imaging.quality.models import QualityAudit

        report = make_report(TENANT)
        audit = QualityAudit.objects.create(
            tenant_id=TENANT,
            report=report,
            auditor_id=RAD2,
            audit_type="peer_review",
            score=2,
            discrepancy_level="major",
            action_required=True,
            action_description="Missed finding — requires educational feedback",
        )
        assert audit.discrepancy_level == "major"
        assert audit.action_required is True

    def test_imaging_quality_metric(self):
        from products.cymed.imaging.quality.models import ImagingQualityMetric

        mod = make_modality(TENANT)
        metric = ImagingQualityMetric.objects.create(
            tenant_id=TENANT,
            modality=mod,
            metric_date=datetime.date.today(),
            repeat_rate=Decimal("2.5"),
            rejection_rate=Decimal("1.2"),
            total_studies=120,
            repeated_studies=3,
        )
        assert metric.repeat_rate == Decimal("2.5")
        assert metric.within_dose_reference is True

    def test_radiation_dose_record(self):
        from products.cymed.imaging.quality.models import RadiationDoseRecord

        item = make_order_item(TENANT)
        dose = RadiationDoseRecord.objects.create(
            tenant_id=TENANT,
            order_item=item,
            patient_id=PATIENT,
            modality="ct",
            ctdivol=Decimal("8.5"),
            dlp=Decimal("425.0"),
            effective_dose_msv=Decimal("6.2"),
        )
        assert dose.effective_dose_msv == Decimal("6.2")
        assert dose.exceeds_drp is False

    def test_accreditation_record(self):
        from products.cymed.imaging.quality.models import AccreditationRecord

        acc = AccreditationRecord.objects.create(
            tenant_id=TENANT,
            accreditation_body="ACR",
            accreditation_type="CT Accreditation",
            certificate_number="ACR-2026-001",
            issue_date=datetime.date(2026, 1, 1),
            expiry_date=datetime.date(2029, 1, 1),
            modality_types=["ct", "mri"],
        )
        assert acc.status == "active"
        assert "ct" in acc.modality_types
