"""
Tests: CyMed Laboratory — Reference Lab, Blood Bank, Analytics, Services
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
        tenant_id=tenant_id, code=f"REF-{uuid.uuid4().hex[:4]}", name="Reference Test"
    )
    order = LabOrder.objects.create(
        tenant_id=tenant_id,
        patient_id=PATIENT,
        ordered_by=PROVIDER,
        order_number=f"ORD-{uuid.uuid4().hex[:8]}",
    )
    return LabOrderItem.objects.create(tenant_id=tenant_id, order=order, test=test)


@pytest.mark.django_db
class TestReferenceLab:
    def test_create_reference_lab(self):
        from products.cymed.laboratory.reference_lab.models import ReferenceLab

        lab = ReferenceLab.objects.create(
            tenant_id=TENANT,
            code="REFLAB-01",
            name="National Reference Laboratory",
            integration_type="fhir",
            sla_tat_hours=48,
        )
        assert lab.status == "active"
        assert lab.is_national is False

    def test_reference_lab_routing(self):
        from products.cymed.laboratory.orders.models import LabTest
        from products.cymed.laboratory.reference_lab.models import ReferenceLab, ReferenceLabRouting

        lab = ReferenceLab.objects.create(
            tenant_id=TENANT,
            code=f"REFLAB-{uuid.uuid4().hex[:4]}",
            name="Ref Lab",
            integration_type="fhir",
        )
        test = LabTest.objects.create(
            tenant_id=TENANT, code=f"MOLTEST-{uuid.uuid4().hex[:4]}", name="Molecular Test"
        )
        routing = ReferenceLabRouting.objects.create(
            tenant_id=TENANT,
            test=test,
            reference_lab=lab,
            is_default=True,
            estimated_tat_hours=72,
        )
        assert routing.is_default is True

    def test_reference_lab_order(self):
        from products.cymed.laboratory.reference_lab.models import ReferenceLab, ReferenceLabOrder

        lab = ReferenceLab.objects.create(
            tenant_id=TENANT,
            code=f"REFLAB-{uuid.uuid4().hex[:4]}",
            name="Ref Lab",
            integration_type="api_rest",
        )
        item = make_order_item(TENANT)
        ref_order = ReferenceLabOrder.objects.create(
            tenant_id=TENANT,
            local_order_item=item,
            reference_lab=lab,
            external_order_id="EXT-00123",
        )
        assert ref_order.status == "pending"

    def test_reference_lab_result(self):
        from products.cymed.laboratory.reference_lab.models import (
            ReferenceLab,
            ReferenceLabOrder,
            ReferenceLabResult,
        )

        lab = ReferenceLab.objects.create(
            tenant_id=TENANT,
            code=f"REFLAB-{uuid.uuid4().hex[:4]}",
            name="Ref Lab",
            integration_type="fhir",
        )
        item = make_order_item(TENANT)
        ref_order = ReferenceLabOrder.objects.create(
            tenant_id=TENANT,
            local_order_item=item,
            reference_lab=lab,
        )
        result = ReferenceLabResult.objects.create(
            tenant_id=TENANT,
            reference_lab_order=ref_order,
            raw_result={"resourceType": "DiagnosticReport"},
            raw_format="fhir",
        )
        assert result.status == "received"


@pytest.mark.django_db
class TestBloodBank:
    def test_blood_product(self):
        from products.cymed.laboratory.blood_bank_foundation.models import BloodProduct

        unit = BloodProduct.objects.create(
            tenant_id=TENANT,
            unit_number="UNIT-001",
            product_type="prbc",
            blood_group="O",
            rh_type="negative",
            expiry_date=datetime.date(2026, 12, 31),
        )
        assert unit.status == "available"

    def test_blood_inventory(self):
        from products.cymed.laboratory.blood_bank_foundation.models import BloodInventory

        inv = BloodInventory.objects.create(
            tenant_id=TENANT,
            product_type="prbc",
            blood_group="O",
            rh_type="negative",
            available_units=10,
            minimum_threshold=2,
        )
        assert inv.available_units == 10

    def test_blood_compatibility(self):
        from products.cymed.laboratory.blood_bank_foundation.models import BloodCompatibility

        compat = BloodCompatibility.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            blood_group="A",
            rh_type="positive",
            antibody_screen="negative",
        )
        assert compat.antibody_screen == "negative"

    def test_transfusion_request(self):
        from products.cymed.laboratory.blood_bank_foundation.models import TransfusionRequest

        req = TransfusionRequest.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            product_type="prbc",
            units_requested=2,
            urgency="urgent",
            requested_by=PROVIDER,
        )
        assert req.status == "pending"


@pytest.mark.django_db
class TestAnalytics:
    def test_ops_dashboard_snapshot(self):
        from products.cymed.laboratory.analytics.models import LabOperationsDashboard

        snap = LabOperationsDashboard.objects.create(
            tenant_id=TENANT,
            snapshot_date=datetime.date.today(),
            department="chemistry",
            total_orders=150,
            orders_completed=145,
            critical_results=3,
            qc_failures=1,
            average_tat_hours=Decimal("2.5"),
        )
        assert snap.total_orders == 150

    def test_tat_metric(self):
        from products.cymed.laboratory.analytics.models import LabTurnaroundMetric

        metric = LabTurnaroundMetric.objects.create(
            tenant_id=TENANT,
            department="hematology",
            test_code="CBC",
            test_name="CBC",
            period_type="daily",
            period_start=datetime.date.today(),
            period_end=datetime.date.today(),
            target_tat_hours=Decimal("1.0"),
            actual_tat_mean_hours=Decimal("0.8"),
            within_target_pct=Decimal("95.0"),
            sample_count=200,
        )
        assert metric.within_target_pct == Decimal("95.0")

    def test_quality_dashboard(self):
        from products.cymed.laboratory.analytics.models import LabQualityDashboard

        dash = LabQualityDashboard.objects.create(
            tenant_id=TENANT,
            period_month=6,
            period_year=2026,
            department="chemistry",
            qc_pass_rate=Decimal("98.5"),
            rejection_rate=Decimal("0.8"),
        )
        assert dash.qc_pass_rate == Decimal("98.5")


@pytest.mark.django_db
class TestFHIRMapping:
    def test_fhir_service_request_mapping(self):
        from products.cymed.laboratory.orders.models import LabOrder
        from products.cymed.laboratory.services import FHIRLabService

        order = LabOrder.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordered_by=PROVIDER,
            order_number="LAB-FHIR-001",
            priority="stat",
        )
        fhir = FHIRLabService.to_fhir_service_request(order)
        assert fhir["resourceType"] == "ServiceRequest"
        assert fhir["priority"] == "stat"
        assert str(PATIENT) in fhir["subject"]["reference"]

    def test_fhir_specimen_mapping(self):
        from products.cymed.laboratory.services import FHIRLabService
        from products.cymed.laboratory.specimens.models import Specimen

        sp = Specimen.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            specimen_number="SP-FHIR-001",
            barcode="BC-FHIR-001",
            specimen_type="blood",
        )
        fhir = FHIRLabService.to_fhir_specimen(sp)
        assert fhir["resourceType"] == "Specimen"
        assert fhir["type"]["text"] == "blood"

    def test_fhir_observation_mapping(self):
        from products.cymed.laboratory.orders.models import LabOrder, LabOrderItem, LabTest
        from products.cymed.laboratory.results.models import LabResult, ResultValue
        from products.cymed.laboratory.services import FHIRLabService

        test = LabTest.objects.create(
            tenant_id=TENANT, code=f"TSH-{uuid.uuid4().hex[:4]}", name="TSH"
        )
        order = LabOrder.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordered_by=PROVIDER,
            order_number=f"ORD-{uuid.uuid4().hex[:8]}",
        )
        item = LabOrderItem.objects.create(tenant_id=TENANT, order=order, test=test)
        result = LabResult.objects.create(tenant_id=TENANT, order_item=item)
        rv = ResultValue.objects.create(
            tenant_id=TENANT,
            result=result,
            analyte_code="TSH",
            analyte_name="Thyroid Stimulating Hormone",
            loinc_code="3016-3",
            value_type="numeric",
            value_numeric=Decimal("2.5"),
            unit="mIU/L",
            interpretation="N",
        )
        obs = FHIRLabService.to_fhir_observation(rv)
        assert obs["resourceType"] == "Observation"
        assert obs["valueQuantity"]["value"] == 2.5


@pytest.mark.django_db
class TestEditionFeatureMap:
    def test_lab_basic_features(self):
        from products.cymed.commercial.feature_flags.services import LAB_BASIC_FEATURES

        assert "lab.orders" in LAB_BASIC_FEATURES
        assert "lab.specimens" in LAB_BASIC_FEATURES
        assert "lab.results" in LAB_BASIC_FEATURES

    def test_lab_advanced_is_superset_of_basic(self):
        from products.cymed.commercial.feature_flags.services import (
            LAB_ADVANCED_FEATURES,
            LAB_BASIC_FEATURES,
        )

        assert all(f in LAB_ADVANCED_FEATURES for f in LAB_BASIC_FEATURES)
        assert "lab.microbiology" in LAB_ADVANCED_FEATURES
        assert "lab.pathology" in LAB_ADVANCED_FEATURES

    def test_lab_reference_is_superset_of_advanced(self):
        from products.cymed.commercial.feature_flags.services import (
            LAB_ADVANCED_FEATURES,
            LAB_REFERENCE_FEATURES,
        )

        assert all(f in LAB_REFERENCE_FEATURES for f in LAB_ADVANCED_FEATURES)
        assert "lab.reference_lab" in LAB_REFERENCE_FEATURES

    def test_edition_feature_map_has_lab_entries(self):
        from products.cymed.commercial.feature_flags.services import EDITION_FEATURE_MAP

        assert "cymed_laboratory:basic" in EDITION_FEATURE_MAP
        assert "cymed_laboratory:advanced" in EDITION_FEATURE_MAP
        assert "cymed_laboratory:reference" in EDITION_FEATURE_MAP
        assert "cymed_laboratory:national" in EDITION_FEATURE_MAP

    def test_qc_service_westgard_13s(self):
        from products.cymed.laboratory.services import QCService

        rules = QCService.WESTGARD_RULES
        assert rules["13s"](3.1, []) is True
        assert rules["13s"](2.9, []) is False

    def test_lab_ordering_service_validates_create(self):
        from products.cymed.laboratory.orders.models import LabTest
        from products.cymed.laboratory.services import LabOrderingService

        LabTest.objects.create(tenant_id=TENANT, code="GLUCX", name="Glucose", is_active=True)
        result = LabOrderingService.create_order(
            tenant_id=TENANT,
            patient_id=PATIENT,
            order_type="clinic",
            tests=["GLUCX"],
            priority="routine",
            ordered_by=PROVIDER,
        )
        assert "order_number" in result
        assert result["order_number"].startswith("LAB-")
