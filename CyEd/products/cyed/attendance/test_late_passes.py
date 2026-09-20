import uuid
from datetime import date, time

import pytest
from rest_framework.test import APIClient

from products.cyed.attendance.models import LatePass
from products.cyed.attendance.services import issue_late_pass
from products.cyed.sis.models import ClassSection, Student


@pytest.fixture
def platform_admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token({
        "sub": str(uuid.uuid4()),
        "email": "reception@cyed.edu.au",
        "tenant_id": str(tenant_id),
        "realm_access": {"roles": ["platform_admin"]},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
def test_issue_late_pass_service(tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Ava", last_name="Lee", year_level=8)
    late_pass = issue_late_pass(
        tenant_id, student=student, arrival_time=time(9, 20), reason="transport",
        reason_detail="Bus delay", issued_by="reception@cyed.edu.au",
    )
    assert late_pass.pass_number.startswith(f"LP-{date.today():%Y%m%d}-")
    assert late_pass.reason == "transport"
    # issuing a pass does not touch attendance rolls at all
    assert LatePass.objects.filter(tenant_id=tenant_id, student=student).count() == 1


@pytest.mark.django_db
def test_issue_via_api_stamps_issuer_and_tenant(platform_admin_client, tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Ben", last_name="Ng", year_level=9)
    resp = platform_admin_client.post(
        "/api/v1/attendance/late-passes/",
        {"student": str(student.id), "arrival_time": "09:15:00", "reason": "medical"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["issued_by"] == "reception@cyed.edu.au"
    assert resp.data["reason_display"] == "Medical appointment"
    assert resp.data["pass_number"]


@pytest.mark.django_db
def test_print_view_returns_html_and_stamps_printed_at(platform_admin_client, tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Cy", last_name="Tran", year_level=10)
    late_pass = issue_late_pass(
        tenant_id, student=student, arrival_time=time(8, 55), reason="overslept",
        issued_by="reception@cyed.edu.au",
    )
    assert late_pass.printed_at is None

    resp = platform_admin_client.get(f"/api/v1/attendance/late-passes/{late_pass.id}/print_view/")
    assert resp.status_code == 200
    assert resp["Content-Type"] == "text/html"
    body = resp.content.decode()
    assert "Cy Tran" in body
    assert late_pass.pass_number in body

    late_pass.refresh_from_db()
    assert late_pass.printed_at is not None


@pytest.mark.django_db
def test_late_passes_scoped_to_tenant(platform_admin_client, tenant_id):
    other_tenant = uuid.uuid4()
    other_student = Student.objects.create(tenant_id=other_tenant, first_name="X", last_name="Y", year_level=7)
    issue_late_pass(other_tenant, student=other_student, arrival_time=time(9, 0), issued_by="x")

    resp = platform_admin_client.get("/api/v1/attendance/late-passes/")
    assert resp.status_code == 200
    rows = resp.data.get("results", resp.data)
    assert rows == []


@pytest.mark.django_db
def test_late_pass_can_name_the_destination_class(tenant_id):
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A Maths", year_level=8)
    student = Student.objects.create(tenant_id=tenant_id, first_name="Dee", last_name="Osei", year_level=8)
    late_pass = issue_late_pass(
        tenant_id, student=student, arrival_time=time(9, 5), class_section=section,
        issued_by="reception@cyed.edu.au",
    )
    assert late_pass.class_section_id == section.id
