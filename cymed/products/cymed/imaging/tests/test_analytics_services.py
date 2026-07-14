"""
Tests: CyMed Imaging — Analytics, Services, FHIR, Edition Feature Maps
"""

import datetime
import uuid
from decimal import Decimal

import pytest

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
PROVIDER = uuid.uuid4()
RAD = uuid.uuid4()


def make_order_item(tenant_id):
    from products.cymed.imaging.orders.models import (
        ImagingOrder,
        ImagingOrderItem,
        ImagingProcedure,
    )

    proc = ImagingProcedure.objects.create(
        tenant_id=tenant_id,
        code=f"PROC-{uuid.uuid4().hex[:4]}",
        name="X-Ray",
        modality="xray",
    )
    order = ImagingOrder.objects.create(
        tenant_id=tenant_id,
        patient_id=PATIENT,
        ordered_by=PROVIDER,
        order_number=f"IMG-{uuid.uuid4().hex[:8].upper()}",
    )
    return ImagingOrderItem.objects.create(tenant_id=tenant_id, order=order, procedure=proc)


@pytest.mark.django_db
class TestAnalytics:
    def test_ops_dashboard(self):
        from products.cymed.imaging.analytics.models import ImagingOperationsDashboard

        dash = ImagingOperationsDashboard.objects.create(
            tenant_id=TENANT,
            snapshot_date=datetime.date.today(),
            department="radiology",
            total_orders=200,
            studies_completed=195,
            reports_finalized=190,
            critical_findings=2,
            average_tat_hours=Decimal("1.8"),
            capacity_utilization_pct=Decimal("85.5"),
        )
        assert dash.total_orders == 200
        assert dash.critical_findings == 2

    def test_radiologist_productivity(self):
        from products.cymed.imaging.analytics.models import RadiologistProductivity

        prod = RadiologistProductivity.objects.create(
            tenant_id=TENANT,
            radiologist_id=RAD,
            period_start=datetime.date.today(),
            period_end=datetime.date.today(),
            period_type="daily",
            total_rvu=Decimal("45.5"),
            studies_read=32,
            reports_finalized=30,
            avg_report_tat_hours=Decimal("0.75"),
            peer_review_score=Decimal("4.2"),
        )
        assert prod.studies_read == 32
        assert prod.total_rvu == Decimal("45.5")

    def test_teleradiology_dashboard(self):
        from products.cymed.imaging.analytics.models import TeleradiologyDashboard

        dash = TeleradiologyDashboard.objects.create(
            tenant_id=TENANT,
            snapshot_date=datetime.date.today(),
            total_cases=50,
            cases_completed=48,
            avg_tat_hours=Decimal("4.2"),
            on_time_rate=Decimal("96.0"),
            second_opinion_requests=5,
            discrepancy_rate=Decimal("3.0"),
        )
        assert dash.on_time_rate == Decimal("96.0")

    def test_imaging_revenue_event(self):
        from products.cymed.imaging.analytics.models import ImagingRevenueEvent

        item_id = uuid.uuid4()
        event = ImagingRevenueEvent.objects.create(
            tenant_id=TENANT,
            order_item_id=item_id,
            patient_id=PATIENT,
            procedure_code="CT-CHEST",
            modality="ct",
            rvu_value=Decimal("3.52"),
            event_type="charge_created",
        )
        assert event.event_type == "charge_created"
        assert event.rvu_value == Decimal("3.52")


@pytest.mark.django_db
class TestFHIRMapping:
    def test_fhir_service_request(self):
        from products.cymed.imaging.orders.models import ImagingOrder
        from products.cymed.imaging.services import FHIRImagingService

        order = ImagingOrder.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordered_by=PROVIDER,
            order_number="IMG-FHIR-001",
            priority="stat",
            order_type="outpatient",
            status="pending",
            clinical_indication="Rule out PE",
        )
        fhir = FHIRImagingService.to_fhir_service_request(order)
        assert fhir["resourceType"] == "ServiceRequest"
        assert fhir["priority"] == "stat"
        assert str(PATIENT) in fhir["subject"]["reference"]
        assert fhir["reasonCode"][0]["text"] == "Rule out PE"

    def test_fhir_diagnostic_report(self):
        from products.cymed.imaging.results.models import ImagingResult
        from products.cymed.imaging.services import FHIRImagingService

        item = make_order_item(TENANT)
        result = ImagingResult.objects.create(
            tenant_id=TENANT,
            order_item=item,
            status="final",
            result_date=datetime.datetime.now(tz=datetime.UTC),
        )
        fhir = FHIRImagingService.to_fhir_diagnostic_report(result)
        assert fhir["resourceType"] == "DiagnosticReport"
        assert fhir["status"] == "final"

    def test_fhir_imaging_study(self):
        from products.cymed.imaging.dicom_registry.models import DICOMStudy
        from products.cymed.imaging.pacs_gateway.models import PACSNode
        from products.cymed.imaging.services import FHIRImagingService

        pacs = PACSNode.objects.create(
            tenant_id=TENANT,
            code=f"PACS-FHIR-{uuid.uuid4().hex[:4]}",
            name="PACS",
            ae_title="P1",
            host="10.0.0.1",
        )
        study = DICOMStudy.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            pacs_node=pacs,
            study_instance_uid=f"1.2.840.{uuid.uuid4().hex}",
            modality="ct",
            study_date=datetime.date.today(),
            series_count=3,
            instance_count=150,
        )
        fhir = FHIRImagingService.to_fhir_imaging_study(study)
        assert fhir["resourceType"] == "ImagingStudy"
        assert fhir["numberOfSeries"] == 3
        assert str(PATIENT) in fhir["subject"]["reference"]


@pytest.mark.django_db
class TestImagingOrderService:
    def test_create_order(self):
        from products.cymed.imaging.orders.models import ImagingProcedure
        from products.cymed.imaging.services import ImagingOrderService

        ImagingProcedure.objects.create(
            tenant_id=TENANT,
            code="CT-HEAD-SVC",
            name="CT Head",
            modality="ct",
            is_active=True,
        )
        result = ImagingOrderService.create_order(
            tenant_id=TENANT,
            patient_id=PATIENT,
            order_type="outpatient",
            procedures=["CT-HEAD-SVC"],
            priority="routine",
            ordered_by=PROVIDER,
            clinical_indication="Headache",
        )
        assert "order_number" in result
        assert result["order_number"].startswith("IMG-")
        assert result["items"] == 1


class TestEditionFeatureMaps:
    def test_imaging_basic_features(self):
        from products.cymed.commercial.feature_flags.services import IMAGING_BASIC_FEATURES

        assert "imaging.orders" in IMAGING_BASIC_FEATURES
        assert "imaging.scheduling" in IMAGING_BASIC_FEATURES
        assert "imaging.reporting" in IMAGING_BASIC_FEATURES

    def test_imaging_enterprise_superset_of_basic(self):
        from products.cymed.commercial.feature_flags.services import (
            IMAGING_BASIC_FEATURES,
            IMAGING_ENTERPRISE_FEATURES,
        )

        assert all(f in IMAGING_ENTERPRISE_FEATURES for f in IMAGING_BASIC_FEATURES)
        assert "imaging.pacs" in IMAGING_ENTERPRISE_FEATURES
        assert "imaging.dicom" in IMAGING_ENTERPRISE_FEATURES
        assert "imaging.analytics" in IMAGING_ENTERPRISE_FEATURES

    def test_imaging_teleradiology_superset_of_enterprise(self):
        from products.cymed.commercial.feature_flags.services import (
            IMAGING_ENTERPRISE_FEATURES,
            IMAGING_TELERADIOLOGY_FEATURES,
        )

        assert all(f in IMAGING_TELERADIOLOGY_FEATURES for f in IMAGING_ENTERPRISE_FEATURES)
        assert "imaging.teleradiology" in IMAGING_TELERADIOLOGY_FEATURES
        assert "imaging.second_opinion" in IMAGING_TELERADIOLOGY_FEATURES

    def test_imaging_national_superset_of_teleradiology(self):
        from products.cymed.commercial.feature_flags.services import (
            IMAGING_NATIONAL_FEATURES,
            IMAGING_TELERADIOLOGY_FEATURES,
        )

        assert all(f in IMAGING_NATIONAL_FEATURES for f in IMAGING_TELERADIOLOGY_FEATURES)
        assert "imaging.national_registry" in IMAGING_NATIONAL_FEATURES

    def test_edition_feature_map_has_imaging_entries(self):
        from products.cymed.commercial.feature_flags.services import EDITION_FEATURE_MAP

        assert "cymed_imaging:basic" in EDITION_FEATURE_MAP
        assert "cymed_imaging:enterprise" in EDITION_FEATURE_MAP
        assert "cymed_imaging:teleradiology" in EDITION_FEATURE_MAP
        assert "cymed_imaging:national" in EDITION_FEATURE_MAP
