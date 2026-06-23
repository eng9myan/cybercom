"""
Tests: CyMed Imaging — Radiology Reporting and Results
"""
import uuid
import pytest
import datetime
from decimal import Decimal

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
PROVIDER = uuid.uuid4()
RAD = uuid.uuid4()


def make_order_item(tenant_id):
    from products.cymed.imaging.orders.models import ImagingOrder, ImagingOrderItem, ImagingProcedure
    proc = ImagingProcedure.objects.create(
        tenant_id=tenant_id, code=f"PROC-{uuid.uuid4().hex[:4]}", name="CT Chest", modality="ct",
    )
    order = ImagingOrder.objects.create(
        tenant_id=tenant_id, patient_id=PATIENT, ordered_by=PROVIDER,
        order_number=f"IMG-{uuid.uuid4().hex[:8].upper()}",
    )
    return ImagingOrderItem.objects.create(tenant_id=tenant_id, order=order, procedure=proc)


@pytest.mark.django_db
class TestReportTemplate:
    def test_create_template(self):
        from products.cymed.imaging.radiology_reporting.models import ReportTemplate
        tmpl = ReportTemplate.objects.create(
            tenant_id=TENANT, name="CT Chest Standard",
            modality="ct", body_part="chest",
            template_text="Technique:\n\nFindings:\n\nImpression:",
            is_structured=False,
        )
        assert tmpl.name == "CT Chest Standard"
        assert tmpl.is_active is True


@pytest.mark.django_db
class TestRadiologyReport:
    def test_create_draft_report(self):
        from products.cymed.imaging.radiology_reporting.models import RadiologyReport
        item = make_order_item(TENANT)
        report = RadiologyReport.objects.create(
            tenant_id=TENANT, order_item=item,
            patient_id=PATIENT, radiologist_id=RAD,
            technique="Standard protocol",
            clinical_indication="Chest pain",
            findings="No acute cardiopulmonary disease",
            impression="Normal chest CT",
        )
        assert report.status == "draft"
        assert report.ai_assistance_used is False

    def test_report_with_ai_summary(self):
        from products.cymed.imaging.radiology_reporting.models import RadiologyReport
        item = make_order_item(TENANT)
        report = RadiologyReport.objects.create(
            tenant_id=TENANT, order_item=item, patient_id=PATIENT, radiologist_id=RAD,
            findings="5mm nodule in right lower lobe",
            impression="Pulmonary nodule requiring follow-up",
            ai_summary="AI: Small pulmonary nodule detected. Recommend Fleischner guideline follow-up.",
            ai_assistance_used=True,
            status="preliminary",
        )
        assert report.ai_assistance_used is True
        assert report.status == "preliminary"

    def test_radiology_finding(self):
        from products.cymed.imaging.radiology_reporting.models import RadiologyReport, RadiologyFinding
        item = make_order_item(TENANT)
        report = RadiologyReport.objects.create(
            tenant_id=TENANT, order_item=item, patient_id=PATIENT, radiologist_id=RAD,
        )
        finding = RadiologyFinding.objects.create(
            tenant_id=TENANT, report=report,
            body_region="right lower lobe", laterality="right",
            description="5mm pulmonary nodule",
            severity="minor", is_incidental=True,
            follow_up_recommended=True,
            follow_up_timeframe="3 months CT",
            size_mm=Decimal("5.0"),
        )
        assert finding.severity == "minor"
        assert finding.follow_up_recommended is True

    def test_radiology_impression(self):
        from products.cymed.imaging.radiology_reporting.models import RadiologyReport, RadiologyImpression
        item = make_order_item(TENANT)
        report = RadiologyReport.objects.create(
            tenant_id=TENANT, order_item=item, patient_id=PATIENT, radiologist_id=RAD,
        )
        imp = RadiologyImpression.objects.create(
            tenant_id=TENANT, report=report,
            impression_number=1,
            impression_text="Pulmonary nodule, likely benign",
            icd11_code="CB00", is_primary=True,
        )
        assert imp.is_primary is True

    def test_critical_finding(self):
        from products.cymed.imaging.radiology_reporting.models import RadiologyReport, CriticalFinding
        item = make_order_item(TENANT)
        report = RadiologyReport.objects.create(
            tenant_id=TENANT, order_item=item, patient_id=PATIENT, radiologist_id=RAD,
        )
        critical = CriticalFinding.objects.create(
            tenant_id=TENANT, report=report,
            finding_description="Large pneumothorax right side",
            severity="emergent",
        )
        assert critical.notification_status == "pending"
        assert critical.severity == "emergent"
        assert critical.read_back_verified is False

    def test_structured_report(self):
        from products.cymed.imaging.radiology_reporting.models import RadiologyReport, StructuredReport
        item = make_order_item(TENANT)
        report = RadiologyReport.objects.create(
            tenant_id=TENANT, order_item=item, patient_id=PATIENT, radiologist_id=RAD,
        )
        sr = StructuredReport.objects.create(
            tenant_id=TENANT, report=report,
            report_schema="LI-RADS", schema_version="2018",
            score="LR-3", category="Intermediate",
            structured_data={"size_mm": 18, "enhancement": "arterial"},
        )
        assert sr.report_schema == "LI-RADS"
        assert sr.score == "LR-3"

    def test_report_amendment(self):
        from products.cymed.imaging.radiology_reporting.models import RadiologyReport, ReportAmendment
        item = make_order_item(TENANT)
        report = RadiologyReport.objects.create(
            tenant_id=TENANT, order_item=item, patient_id=PATIENT, radiologist_id=RAD,
            status="final", findings="No acute findings",
            impression="Normal",
        )
        amendment = ReportAmendment.objects.create(
            tenant_id=TENANT, original_report=report,
            amended_by=RAD,
            amendment_reason="Additional finding identified on review",
            previous_findings="No acute findings",
            previous_impression="Normal",
            new_findings="No acute findings. 3mm nodule right lower lobe.",
            new_impression="Incidental pulmonary nodule.",
            is_significant=True,
        )
        assert amendment.is_significant is True


@pytest.mark.django_db
class TestImagingResults:
    def test_imaging_result(self):
        from products.cymed.imaging.results.models import ImagingResult
        item = make_order_item(TENANT)
        result = ImagingResult.objects.create(
            tenant_id=TENANT, order_item=item, status="pending",
        )
        assert result.status == "pending"

    def test_structured_measurement(self):
        from products.cymed.imaging.results.models import ImagingResult, StructuredMeasurement
        item = make_order_item(TENANT)
        result = ImagingResult.objects.create(tenant_id=TENANT, order_item=item)
        meas = StructuredMeasurement.objects.create(
            tenant_id=TENANT, result=result,
            measurement_name="Aortic diameter",
            value=Decimal("32.5"), unit="mm",
            body_site="ascending aorta",
            reference_range_high=Decimal("40.0"),
        )
        assert meas.value == Decimal("32.5")
        assert meas.unit == "mm"

    def test_result_communication(self):
        from products.cymed.imaging.results.models import ImagingResult, ResultCommunication
        item = make_order_item(TENANT)
        result = ImagingResult.objects.create(tenant_id=TENANT, order_item=item, status="final")
        comm = ResultCommunication.objects.create(
            tenant_id=TENANT, result=result,
            communicated_to=PROVIDER, communicated_by=RAD,
            communication_method="portal",
        )
        assert comm.acknowledged is False
