"""Hierarchical departments: tree, roll-up counts, cycle and delete guards,
and the legacy free-text Employee.department kept in sync."""
import uuid
from datetime import date

import pytest
from rest_framework.test import APIClient

from products.cycom.hr.models import Department, Employee

pytestmark = pytest.mark.django_db


@pytest.fixture
def client(mint_token, mock_jwks, tenant_id):
    token = mint_token({"sub": str(uuid.uuid4()), "tenant_id": str(tenant_id),
                        "realm_access": {"roles": ["tenant_admin"]}})
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return c


def _emp(tid, n, **kw):
    return Employee.objects.create(tenant_id=tid, employee_number=f"E{n}", first_name="F", last_name=str(n),
                                   hire_date=date(2026, 1, 1), **kw)


def test_tree_with_rollup_counts_and_manager(client, tenant_id):
    ops = client.post("/api/v1/hr/departments/", {"name": "Operations"}, format="json").data
    wh = client.post("/api/v1/hr/departments/", {"name": "Warehouse", "parent": ops["id"]}, format="json").data
    boss = _emp(tenant_id, 1, department_unit_id=ops["id"])
    _emp(tenant_id, 2, department_unit_id=wh["id"])
    _emp(tenant_id, 3, department_unit_id=wh["id"])
    _emp(tenant_id, 4, department_unit_id=wh["id"], status="terminated")   # not counted
    client.patch(f"/api/v1/hr/departments/{ops['id']}/", {"manager": str(boss.id)}, format="json")

    rows = {d["name"]: d for d in client.get("/api/v1/hr/departments/").data}
    assert rows["Operations"]["member_count"] == 1
    assert rows["Operations"]["total_employee"] == 3
    assert rows["Warehouse"]["total_employee"] == 2
    assert rows["Operations"]["child_ids"] == [wh["id"]]
    assert rows["Operations"]["manager_name"] == "F 1"


def test_cycles_are_refused(client):
    a = client.post("/api/v1/hr/departments/", {"name": "A"}, format="json").data
    b = client.post("/api/v1/hr/departments/", {"name": "B", "parent": a["id"]}, format="json").data
    assert client.patch(f"/api/v1/hr/departments/{a['id']}/", {"parent": b["id"]}, format="json").status_code == 400
    assert client.patch(f"/api/v1/hr/departments/{a['id']}/", {"parent": a["id"]}, format="json").status_code == 400


def test_delete_is_refused_while_it_has_children_or_members(client, tenant_id):
    a = client.post("/api/v1/hr/departments/", {"name": "A"}, format="json").data
    b = client.post("/api/v1/hr/departments/", {"name": "B", "parent": a["id"]}, format="json").data
    assert client.delete(f"/api/v1/hr/departments/{a['id']}/").status_code == 400
    emp = _emp(tenant_id, 9, department_unit_id=b["id"])
    assert client.delete(f"/api/v1/hr/departments/{b['id']}/").status_code == 400
    emp.department_unit = None
    emp.department = ""
    emp.save()
    assert client.delete(f"/api/v1/hr/departments/{b['id']}/").status_code == 204


def test_text_and_fk_stay_in_sync(tenant_id):
    sales = Department.objects.create(tenant_id=tenant_id, name="Sales")
    by_text = _emp(tenant_id, 1, department="Sales")
    assert by_text.department_unit_id == sales.id                     # text links to the unit
    by_fk = _emp(tenant_id, 2, department_unit=sales)
    assert by_fk.department == "Sales"                                 # unit sets the text


def test_other_tenants_department_cannot_be_used(client, tenant_id):
    theirs = Department.objects.create(tenant_id=uuid.uuid4(), name="Theirs")
    resp = client.post("/api/v1/hr/departments/", {"name": "Mine", "parent": str(theirs.id)}, format="json")
    assert resp.status_code == 400


def test_backfill_migration_creates_units_from_existing_text(tenant_id):
    import importlib

    from django.apps import apps

    Employee.objects.create(tenant_id=tenant_id, employee_number="L1", first_name="a", last_name="b",
                            hire_date=date(2026, 1, 1), department="Legacy Dept")
    Employee.objects.filter(employee_number="L1").update(department_unit=None)
    Department.objects.filter(name="Legacy Dept").delete()
    mod = importlib.import_module("products.cycom.hr.migrations.0009_backfill_departments")
    mod.forwards(apps, None)
    emp = Employee.objects.get(employee_number="L1")
    assert emp.department_unit and emp.department_unit.name == "Legacy Dept"
