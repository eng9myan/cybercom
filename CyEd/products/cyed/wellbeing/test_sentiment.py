import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.sis.models import Student
from products.cyed.wellbeing.models import WellbeingCheckIn
from products.cyed.wellbeing.sentiment import analyse


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


def test_analyse_labels():
    assert analyse("I had a great day, feeling happy and confident")[1] == "positive"
    assert analyse("I feel sad, stressed and overwhelmed")[1] == "negative"
    score, label, flagged = analyse("I feel hopeless and alone, being bullied")
    assert label == "distress" and flagged is True


@pytest.mark.django_db
def test_checkin_computes_and_flags(client_for, tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8,
                                     email="ivy@student.cyed.edu.au")
    stu = client_for(["student"], email="ivy@student.cyed.edu.au")
    resp = stu.post("/api/v1/wellbeing/checkins/",
                    {"student": str(student.id), "response_text": "I feel hopeless and bullied and alone"},
                    format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["sentiment_label"] == "distress"
    assert resp.data["flagged"] is True


@pytest.mark.django_db
def test_reads_are_pastoral_only(client_for, tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8)
    WellbeingCheckIn.objects.create(tenant_id=tenant_id, student=student, response_text="sad and stressed",
                                    sentiment_label="negative", flagged=True)

    teacher = client_for(["teacher"])
    assert teacher.get("/api/v1/wellbeing/checkins/").status_code == 403

    pastoral = client_for(["counsellor"])
    flagged = pastoral.get("/api/v1/wellbeing/checkins/?flagged=1")
    assert flagged.status_code == 200
    rows = flagged.data["results"] if isinstance(flagged.data, dict) else flagged.data
    assert len(rows) == 1

    cohort = pastoral.get("/api/v1/wellbeing/checkins/cohort/?year_level=8")
    assert cohort.status_code == 200
    assert cohort.data["flagged"] == 1
