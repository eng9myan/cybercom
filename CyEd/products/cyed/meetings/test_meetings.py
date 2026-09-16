import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.meetings.summarise import summarise


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


def test_summarise_extracts_action_items():
    t = ("Ivy is progressing well in mathematics. "
         "The teacher will send extra practice sheets. "
         "Parent to schedule a follow up in week 6. "
         "Ivy enjoys group work.")
    r = summarise(t)
    assert any("send" in a.lower() for a in r["action_items"])
    assert any("schedule" in a.lower() or "follow up" in a.lower() for a in r["action_items"])
    assert r["summary"]


@pytest.mark.django_db
def test_create_meeting_summarises(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    resp = admin.post("/api/v1/meetings/sessions/", {
        "title": "Parent-teacher — Ivy", "meeting_type": "parent_teacher",
        "transcript": "Teacher will email the reading list. Parent should book a review next term.",
    }, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["status"] == "summarised"
    assert len(resp.data["action_items"]) >= 1


@pytest.mark.django_db
def test_confidential_hidden_from_non_pastoral(client_for, tenant_id):
    from products.cyed.meetings.models import MeetingSession
    MeetingSession.objects.create(tenant_id=tenant_id, title="Counselling", meeting_type="counselling",
                                  is_confidential=True, transcript="x")

    teacher = client_for(["teacher"])
    rows = teacher.get("/api/v1/meetings/sessions/").data
    rows = rows["results"] if isinstance(rows, dict) else rows
    assert len(rows) == 0  # confidential hidden

    pastoral = client_for(["counsellor"])
    prows = pastoral.get("/api/v1/meetings/sessions/").data
    prows = prows["results"] if isinstance(prows, dict) else prows
    assert len(prows) == 1
