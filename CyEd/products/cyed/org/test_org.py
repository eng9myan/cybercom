import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.billing.models import Installment, StudentBill
from products.cyed.hr.models import Staff
from products.cyed.org.models import Campus
from products.cyed.sis.models import ClassSection, Student


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


@pytest.mark.django_db
def test_campus_crud_staff_only(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    r = admin.post("/api/v1/org/campuses/",
                   {"name": "Melbourne Senior", "code": "MEL", "state": "VIC"}, format="json")
    assert r.status_code == 201, r.data
    assert r.data["name"] == "Melbourne Senior"

    parent = client_for(["parent"])
    denied = parent.post("/api/v1/org/campuses/", {"name": "Hack", "code": "X"}, format="json")
    assert denied.status_code == 403


@pytest.mark.django_db
def test_campus_code_unique_per_group(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    Campus.objects.create(tenant_id=tenant_id, name="A", code="DUP")
    r = admin.post("/api/v1/org/campuses/", {"name": "B", "code": "DUP"}, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_group_rollup_aggregates_per_campus(client_for, tenant_id):
    principal = client_for(["principal"])
    c1 = Campus.objects.create(tenant_id=tenant_id, name="North", code="N", state="NSW")
    c2 = Campus.objects.create(tenant_id=tenant_id, name="South", code="S", state="NSW")

    Student.objects.create(tenant_id=tenant_id, first_name="A", last_name="One", year_level=7, campus=c1)
    Student.objects.create(tenant_id=tenant_id, first_name="B", last_name="Two", year_level=8, campus=c1)
    Student.objects.create(tenant_id=tenant_id, first_name="C", last_name="Three", year_level=9, campus=c2)
    Student.objects.create(tenant_id=tenant_id, first_name="D", last_name="Four", year_level=9)  # unassigned
    Staff.objects.create(tenant_id=tenant_id, first_name="T", last_name="Eacher", campus=c1)
    ClassSection.objects.create(tenant_id=tenant_id, name="7A", year_level=7, campus=c1)

    bill = StudentBill.objects.create(tenant_id=tenant_id,
                                      student=Student.objects.filter(campus=c2).first(), campus=c2)
    Installment.objects.create(tenant_id=tenant_id, bill=bill, installment_no=1,
                               amount_due=500, status="unpaid")

    r = principal.get("/api/v1/org/rollup/")
    assert r.status_code == 200, r.data
    totals = r.data["group_totals"]
    assert totals["campuses"] == 2
    assert totals["students"] == 3  # unassigned not counted per-campus
    assert totals["students_unassigned_campus"] == 1
    assert totals["staff"] == 1
    assert totals["classes"] == 1
    assert totals["fees_outstanding"] == "500.00"

    north = next(row for row in r.data["campuses"] if row["name"] == "North")
    assert north["students"] == 2


@pytest.mark.django_db
def test_group_rollup_forbidden_for_teacher(client_for, tenant_id):
    teacher = client_for(["teacher"])
    r = teacher.get("/api/v1/org/rollup/")
    assert r.status_code == 403
