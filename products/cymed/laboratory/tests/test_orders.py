"""
Tests: CyMed Laboratory — Order Management
"""

import uuid

import pytest
from django.test import RequestFactory

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
PROVIDER = uuid.uuid4()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def tenant_id():
    return TENANT


@pytest.mark.django_db
class TestLabTest:
    def test_create_lab_test(self):
        from products.cymed.laboratory.orders.models import LabTest

        t = LabTest.objects.create(
            tenant_id=TENANT,
            code="CBC",
            name="Complete Blood Count",
            loinc_code="58410-2",
            category="hematology",
            specimen_types_accepted=["blood"],
            turn_around_hours=4,
        )
        assert t.code == "CBC"
        assert t.loinc_code == "58410-2"
        assert t.is_active is True

    def test_lab_test_str(self):
        from products.cymed.laboratory.orders.models import LabTest

        t = LabTest.objects.create(tenant_id=TENANT, code="BMP", name="Basic Metabolic Panel")
        assert "BMP" in str(t)

    def test_lab_panel_with_tests(self):
        from products.cymed.laboratory.orders.models import LabPanel, LabTest

        t1 = LabTest.objects.create(tenant_id=TENANT, code="NA", name="Sodium")
        t2 = LabTest.objects.create(tenant_id=TENANT, code="K", name="Potassium")
        panel = LabPanel.objects.create(
            tenant_id=TENANT, code="ELECTROLYTES", name="Electrolyte Panel"
        )
        panel.tests.add(t1, t2)
        assert panel.tests.count() == 2


@pytest.mark.django_db
class TestLabOrder:
    def test_create_order(self):
        from products.cymed.laboratory.orders.models import LabOrder

        order = LabOrder.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordered_by=PROVIDER,
            order_number="LAB-001",
            order_type="clinic",
            priority="routine",
        )
        assert order.status == "submitted"
        assert str(order) == "LAB-001"

    def test_order_items(self):
        from products.cymed.laboratory.orders.models import LabOrder, LabOrderItem, LabTest

        test = LabTest.objects.create(tenant_id=TENANT, code="TSH", name="TSH")
        order = LabOrder.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordered_by=PROVIDER,
            order_number="LAB-002",
            order_type="clinic",
        )
        item = LabOrderItem.objects.create(
            tenant_id=TENANT,
            order=order,
            test=test,
            priority="stat",
        )
        assert item.status == "ordered"
        assert order.items.count() == 1

    def test_order_diagnosis(self):
        from products.cymed.laboratory.orders.models import LabOrder, LabOrderDiagnosis

        order = LabOrder.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordered_by=PROVIDER,
            order_number="LAB-003",
        )
        diag = LabOrderDiagnosis.objects.create(
            tenant_id=TENANT, order=order, icd11_code="B20", description="HIV", is_primary=True
        )
        assert diag.is_primary is True

    def test_order_status_history(self):
        from products.cymed.laboratory.orders.models import LabOrder, LabOrderStatusHistory

        order = LabOrder.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordered_by=PROVIDER,
            order_number="LAB-004",
        )
        h = LabOrderStatusHistory.objects.create(
            tenant_id=TENANT, order=order, from_status="", to_status="submitted"
        )
        assert h.to_status == "submitted"

    def test_stat_priority(self):
        from products.cymed.laboratory.orders.models import LabOrder, LabPriority

        order = LabOrder.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordered_by=PROVIDER,
            order_number="LAB-005",
            priority=LabPriority.STAT,
        )
        assert order.priority == "stat"

    def test_tenant_isolation(self):
        from products.cymed.laboratory.orders.models import LabOrder

        other_tenant = uuid.uuid4()
        LabOrder.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            ordered_by=PROVIDER,
            order_number="LAB-006",
        )
        LabOrder.objects.create(
            tenant_id=other_tenant,
            patient_id=PATIENT,
            ordered_by=PROVIDER,
            order_number="LAB-007",
        )
        assert LabOrder.objects.filter(tenant_id=TENANT).count() == 1
        assert LabOrder.objects.filter(tenant_id=other_tenant).count() == 1
