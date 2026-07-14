"""
Tests: CyMed Laboratory — Result Management, Critical Values, QC
"""

import datetime
import uuid
from decimal import Decimal

import pytest

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
PROVIDER = uuid.uuid4()


def make_order_item(tenant_id):
    from products.cymed.laboratory.orders.models import LabOrder, LabOrderItem, LabTest

    test = LabTest.objects.create(
        tenant_id=tenant_id, code=f"TEST-{uuid.uuid4().hex[:4]}", name="Test"
    )
    order = LabOrder.objects.create(
        tenant_id=tenant_id,
        patient_id=PATIENT,
        ordered_by=PROVIDER,
        order_number=f"ORD-{uuid.uuid4().hex[:8]}",
    )
    return LabOrderItem.objects.create(tenant_id=tenant_id, order=order, test=test)


@pytest.mark.django_db
class TestLabResult:
    def test_create_result(self):
        from products.cymed.laboratory.results.models import LabResult, ResultStatus

        item = make_order_item(TENANT)
        result = LabResult.objects.create(tenant_id=TENANT, order_item=item)
        assert result.status == ResultStatus.PENDING
        assert result.has_critical_value is False

    def test_result_value_numeric(self):
        from products.cymed.laboratory.results.models import LabResult, ResultValue

        item = make_order_item(TENANT)
        result = LabResult.objects.create(tenant_id=TENANT, order_item=item)
        rv = ResultValue.objects.create(
            tenant_id=TENANT,
            result=result,
            analyte_code="HGB",
            analyte_name="Hemoglobin",
            loinc_code="718-7",
            value_type="numeric",
            value_numeric=Decimal("14.5"),
            unit="g/dL",
            interpretation="N",
        )
        assert rv.is_critical is False
        assert rv.interpretation == "N"

    def test_critical_result_creation(self):
        from products.cymed.laboratory.results.models import CriticalResult, LabResult, ResultValue

        item = make_order_item(TENANT)
        result = LabResult.objects.create(tenant_id=TENANT, order_item=item)
        rv = ResultValue.objects.create(
            tenant_id=TENANT,
            result=result,
            analyte_code="K",
            analyte_name="Potassium",
            value_type="numeric",
            value_numeric=Decimal("6.8"),
            unit="mEq/L",
            interpretation="HH",
            is_critical=True,
        )
        cr = CriticalResult.objects.create(tenant_id=TENANT, result_value=rv)
        assert cr.notification_status == "pending"

    def test_reference_range(self):
        from products.cymed.laboratory.orders.models import LabTest
        from products.cymed.laboratory.results.models import ReferenceRange

        test = LabTest.objects.create(
            tenant_id=TENANT, code=f"HGB-{uuid.uuid4().hex[:4]}", name="Hemoglobin"
        )
        rr = ReferenceRange.objects.create(
            tenant_id=TENANT,
            test=test,
            sex="M",
            age_min_years=Decimal("18"),
            age_max_years=Decimal("65"),
            value_low=Decimal("13.5"),
            value_high=Decimal("17.5"),
            critical_low=Decimal("7.0"),
            critical_high=Decimal("20.0"),
            unit="g/dL",
        )
        assert rr.value_low == Decimal("13.5")

    def test_result_approval(self):
        from products.cymed.laboratory.results.models import LabResult, ResultApproval

        item = make_order_item(TENANT)
        result = LabResult.objects.create(tenant_id=TENANT, order_item=item)
        approval = ResultApproval.objects.create(
            tenant_id=TENANT,
            result=result,
            approval_level="pathologist",
            approved_by=PROVIDER,
        )
        assert approval.signature_method == "pin"

    def test_result_correction(self):
        from products.cymed.laboratory.results.models import LabResult, ResultCorrection

        item = make_order_item(TENANT)
        result = LabResult.objects.create(tenant_id=TENANT, order_item=item)
        corr = ResultCorrection.objects.create(
            tenant_id=TENANT,
            result=result,
            analyte_code="NA",
            original_value="125",
            corrected_value="135",
            correction_reason="Transcription error",
            corrected_by=PROVIDER,
        )
        assert corr.corrected_value == "135"


@pytest.mark.django_db
class TestQualityControl:
    def test_create_qc_material(self):
        from products.cymed.laboratory.orders.models import LabTest
        from products.cymed.laboratory.quality.models import QualityControl

        test = LabTest.objects.create(
            tenant_id=TENANT, code=f"QC-TST-{uuid.uuid4().hex[:4]}", name="QC Test"
        )
        qc = QualityControl.objects.create(
            tenant_id=TENANT,
            test=test,
            lot_number="LOT-2026-001",
            level="L2",
            target_mean=Decimal("5.0"),
            target_sd=Decimal("0.25"),
            expiry_date=datetime.date(2026, 12, 31),
        )
        assert qc.level == "L2"

    def test_qc_run_pass(self):
        from products.cymed.laboratory.orders.models import LabTest
        from products.cymed.laboratory.quality.models import QualityControl, QualityRun

        test = LabTest.objects.create(
            tenant_id=TENANT, code=f"QC-TST-{uuid.uuid4().hex[:4]}", name="QC Test"
        )
        qc = QualityControl.objects.create(
            tenant_id=TENANT,
            test=test,
            lot_number=f"LOT-{uuid.uuid4().hex[:6]}",
            level="L2",
            target_mean=Decimal("10.0"),
            target_sd=Decimal("0.5"),
            expiry_date=datetime.date(2026, 12, 31),
        )
        run = QualityRun.objects.create(
            tenant_id=TENANT,
            qc=qc,
            run_date=datetime.date.today(),
            run_time=datetime.time(8, 0),
            technologist_id=PROVIDER,
            measured_value=Decimal("10.3"),
            z_score=Decimal("0.6"),
            passed=True,
        )
        assert run.passed is True

    def test_qc_failure_creates_record(self):
        from products.cymed.laboratory.orders.models import LabTest
        from products.cymed.laboratory.quality.models import (
            QualityControl,
            QualityFailure,
            QualityRun,
        )

        test = LabTest.objects.create(
            tenant_id=TENANT, code=f"QC-TST-{uuid.uuid4().hex[:4]}", name="QC Test"
        )
        qc = QualityControl.objects.create(
            tenant_id=TENANT,
            test=test,
            lot_number=f"LOT-{uuid.uuid4().hex[:6]}",
            level="L1",
            target_mean=Decimal("5.0"),
            target_sd=Decimal("0.2"),
            expiry_date=datetime.date(2026, 12, 31),
        )
        run = QualityRun.objects.create(
            tenant_id=TENANT,
            qc=qc,
            run_date=datetime.date.today(),
            run_time=datetime.time(9, 0),
            technologist_id=PROVIDER,
            measured_value=Decimal("5.7"),
            z_score=Decimal("3.5"),
            passed=False,
            is_rejection=True,
        )
        QualityFailure.objects.create(tenant_id=TENANT, qc_run=run)
        assert QualityFailure.objects.filter(qc_run=run).count() == 1
