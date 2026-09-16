import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.hr.models import Staff
from products.cyed.org.models import Campus
from products.cyed.sis.imports import import_staff, import_students
from products.cyed.sis.models import Student


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


STUDENT_CSV = (
    "first_name,last_name,student_number,year_level,email,indigenous_status,lbote,campus_code\n"
    "Ava,Smith,S001,7,ava@x.com,4,false,MEL\n"
    "Liam,Nguyen,S002,8,liam@x.com,4,true,MEL\n"
    ",Missing,S003,9,,9,false,MEL\n"          # error: no first name
    "Noah,Brown,S004,7,noah@x.com,4,false,ZZZ\n"  # error: unknown campus
).encode()


@pytest.mark.django_db
def test_import_students_service(tenant_id):
    Campus.objects.create(tenant_id=tenant_id, name="Melbourne", code="MEL")
    report = import_students(tenant_id, STUDENT_CSV)
    assert report["created"] == 2
    assert report["updated"] == 0
    assert len(report["errors"]) == 2
    ava = Student.objects.get(tenant_id=tenant_id, student_number="S001")
    assert ava.campus.code == "MEL"
    assert Student.objects.get(tenant_id=tenant_id, student_number="S002").lbote is True


@pytest.mark.django_db
def test_import_students_idempotent(tenant_id):
    Campus.objects.create(tenant_id=tenant_id, name="Melbourne", code="MEL")
    import_students(tenant_id, STUDENT_CSV)
    report2 = import_students(tenant_id, STUDENT_CSV)
    assert report2["created"] == 0
    assert report2["updated"] == 2  # re-import updates, no duplicates
    assert Student.objects.filter(tenant_id=tenant_id).count() == 2


@pytest.mark.django_db
def test_import_students_endpoint_staff_only(client_for, tenant_id):
    from django.core.files.uploadedfile import SimpleUploadedFile

    Campus.objects.create(tenant_id=tenant_id, name="Melbourne", code="MEL")
    f = SimpleUploadedFile("students.csv", STUDENT_CSV, content_type="text/csv")
    admin = client_for(["tenant_admin"])
    r = admin.post("/api/v1/sis/students/import/", {"file": f}, format="multipart")
    assert r.status_code == 200, r.data
    assert r.data["created"] == 2

    parent = client_for(["parent"])
    f2 = SimpleUploadedFile("students.csv", STUDENT_CSV, content_type="text/csv")
    denied = parent.post("/api/v1/sis/students/import/", {"file": f2}, format="multipart")
    assert denied.status_code == 403


@pytest.mark.django_db
def test_import_staff_service(tenant_id):
    csv_bytes = (
        "first_name,last_name,staff_number,email,role,department\n"
        "Jane,Doe,T001,jane@x.com,teacher,Science\n"
        "Sam,Ray,T002,sam@x.com,leadership,Exec\n"
    ).encode()
    report = import_staff(tenant_id, csv_bytes)
    assert report["created"] == 2
    assert Staff.objects.get(tenant_id=tenant_id, staff_number="T002").role == "leadership"
