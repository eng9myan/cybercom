import uuid
from datetime import date

import pytest
from rest_framework.test import APIClient

from products.cyed.attendance.models import AttendanceMark, RollCall
from products.cyed.gradebook.models import Assessment, Grade
from products.cyed.sis.models import ClassSection, Student
from products.cyed.wellbeing.models import BehaviourIncident


@pytest.fixture
def platform_admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "counsellor@cyed.edu.au",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
def test_at_risk_flags_struggling_student(platform_admin_client, tenant_id):
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A", year_level=8)
    # At-risk student: high absence + low grade + major incident.
    risky = Student.objects.create(tenant_id=tenant_id, first_name="Sam", last_name="Low", year_level=8)
    # Healthy student: present + good grade.
    ok = Student.objects.create(tenant_id=tenant_id, first_name="Alex", last_name="High", year_level=8)

    rc = RollCall.objects.create(tenant_id=tenant_id, class_section=section, date=date.today())
    for i in range(10):
        rc_i = RollCall.objects.create(tenant_id=tenant_id, class_section=section, date=date.today(), period_label=f"P{i}")
        AttendanceMark.objects.create(tenant_id=tenant_id, roll_call=rc_i, student=risky,
                                      status="absent" if i < 6 else "present")
        AttendanceMark.objects.create(tenant_id=tenant_id, roll_call=rc_i, student=ok, status="present")

    a = Assessment.objects.create(tenant_id=tenant_id, class_section=section, name="Test", max_score=100)
    Grade.objects.create(tenant_id=tenant_id, assessment=a, student=risky, score=35)
    Grade.objects.create(tenant_id=tenant_id, assessment=a, student=ok, score=88)
    BehaviourIncident.objects.create(tenant_id=tenant_id, student=risky, date=date.today(), category="major")

    resp = platform_admin_client.get("/api/v1/analytics/at-risk/")
    assert resp.status_code == 200, resp.data
    by_id = {r["student_id"]: r for r in resp.data["students"]}
    assert by_id[str(risky.id)]["risk_band"] == "high"
    assert by_id[str(ok.id)]["risk_band"] == "low"
    assert any("absence" in f.lower() for f in by_id[str(risky.id)]["factors"])
    assert resp.data["summary"]["high"] == 1


@pytest.mark.django_db
def test_at_risk_band_filter(platform_admin_client, tenant_id):
    Student.objects.create(tenant_id=tenant_id, first_name="Nil", last_name="Data", year_level=7)
    resp = platform_admin_client.get("/api/v1/analytics/at-risk/?band=high")
    assert resp.status_code == 200
    assert all(r["risk_band"] == "high" for r in resp.data["students"])
