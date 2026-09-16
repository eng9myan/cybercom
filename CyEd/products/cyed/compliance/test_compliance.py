import uuid

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.attendance.models import AttendanceMark, RollCall
from products.cyed.compliance.models import NCCDRecord, StatutoryReportLog
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
def test_nccd_record_pastoral_only(client_for, tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="A", last_name="One", year_level=7)
    counsellor = client_for(["counsellor"])
    r = counsellor.post("/api/v1/compliance/nccd-records/",
                        {"student": str(student.id), "collection_year": 2026,
                         "category": "cognitive", "level_of_adjustment": "supplementary"}, format="json")
    assert r.status_code == 201, r.data

    teacher = client_for(["teacher"])
    denied = teacher.post("/api/v1/compliance/nccd-records/",
                          {"student": str(student.id), "collection_year": 2026,
                           "category": "physical", "level_of_adjustment": "substantial"}, format="json")
    assert denied.status_code == 403


@pytest.mark.django_db
def test_nccd_record_unique_per_year(client_for, tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="A", last_name="One", year_level=7)
    NCCDRecord.objects.create(tenant_id=tenant_id, student=student, collection_year=2026,
                              category="cognitive", level_of_adjustment="supplementary")
    admin = client_for(["tenant_admin"])
    r = admin.post("/api/v1/compliance/nccd-records/",
                   {"student": str(student.id), "collection_year": 2026,
                    "category": "sensory", "level_of_adjustment": "extensive"}, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_nccd_export_leadership_only_and_logs(client_for, tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Sam", last_name="Lee", year_level=8)
    NCCDRecord.objects.create(tenant_id=tenant_id, student=student, collection_year=2026,
                              category="cognitive", level_of_adjustment="substantial")

    teacher = client_for(["teacher"])
    assert teacher.get("/api/v1/compliance/exports/nccd/?year=2026").status_code == 403

    principal = client_for(["principal"])
    r = principal.get("/api/v1/compliance/exports/nccd/?year=2026")
    assert r.status_code == 200, r.data
    assert r.data["count"] == 1
    assert r.data["rows"][0]["surname"] == "Lee"
    assert StatutoryReportLog.objects.filter(tenant_id=tenant_id, report_type="nccd").count() == 1


@pytest.mark.django_db
def test_nccd_export_csv(client_for, tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Sam", last_name="Lee", year_level=8)
    NCCDRecord.objects.create(tenant_id=tenant_id, student=student, collection_year=2026,
                              category="cognitive", level_of_adjustment="substantial")
    principal = client_for(["principal"])
    r = principal.get("/api/v1/compliance/exports/nccd/?year=2026&fmt=csv")
    assert r.status_code == 200
    assert r["Content-Type"].startswith("text/csv")
    assert "Lee" in r.content.decode()


@pytest.mark.django_db
def test_attendance_return_rate(client_for, tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Ng", year_level=7)
    section = ClassSection.objects.create(tenant_id=tenant_id, name="7A", year_level=7)
    for i, st in enumerate(["present", "present", "absent", "late"]):
        rc = RollCall.objects.create(tenant_id=tenant_id, class_section=section,
                                     date=timezone.now().date(), period_label=f"P{i}")
        AttendanceMark.objects.create(tenant_id=tenant_id, roll_call=rc, student=student, status=st)

    principal = client_for(["principal"])
    r = principal.get("/api/v1/compliance/exports/attendance/")
    assert r.status_code == 200, r.data
    row = r.data["rows"][0]
    # present + late + left_early = 3 of 4 = 75.0
    assert row["attendance_rate"] == "75.0"
    assert row["sessions_possible"] == 4


@pytest.mark.django_db
def test_naplan_participation_cohort(client_for, tenant_id):
    Student.objects.create(tenant_id=tenant_id, first_name="A", last_name="Y7", year_level=7,
                           enrolment_status="enrolled", usi="ABC123")
    Student.objects.create(tenant_id=tenant_id, first_name="B", last_name="Y8", year_level=8,
                           enrolment_status="enrolled")  # not a NAPLAN year
    principal = client_for(["principal"])
    r = principal.get("/api/v1/compliance/exports/naplan/")
    assert r.status_code == 200, r.data
    assert r.data["count"] == 1
    assert r.data["rows"][0]["year_level"] == 7
    assert r.data["rows"][0]["participation"] == "P"


@pytest.mark.django_db
def test_census_demographics(client_for, tenant_id):
    Student.objects.create(tenant_id=tenant_id, first_name="C", last_name="Kaur", year_level=9,
                           enrolment_status="enrolled", indigenous_status="4", lbote=True,
                           language_at_home="Punjabi", country_of_birth="Australia")
    principal = client_for(["principal"])
    r = principal.get("/api/v1/compliance/exports/census/")
    assert r.status_code == 200, r.data
    row = r.data["rows"][0]
    assert row["lbote"] is True
    assert row["language_at_home"] == "Punjabi"
    assert row["indigenous_status"] == "4"
