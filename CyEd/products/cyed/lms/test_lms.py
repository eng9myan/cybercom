import uuid

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def platform_admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "admin@cyed.edu.au",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
def test_course_module_lesson_tree(platform_admin_client, tenant_id):
    c = platform_admin_client.post(
        "/api/v1/lms/courses/",
        {"name": "Year 8 Mathematics", "subject": "Mathematics", "year_level": 8, "is_published": True},
        format="json",
    )
    assert c.status_code == 201, c.data
    course_id = c.data["id"]

    m = platform_admin_client.post(
        "/api/v1/lms/modules/",
        {"course": course_id, "name": "Number & Algebra", "sequence": 1},
        format="json",
    )
    assert m.status_code == 201, m.data
    module_id = m.data["id"]

    lesson = platform_admin_client.post(
        "/api/v1/lms/lessons/",
        {"module": module_id, "title": "Irrational Numbers", "curriculum_code": "AC9M8N01",
         "sequence": 1, "is_published": True},
        format="json",
    )
    assert lesson.status_code == 201, lesson.data

    detail = platform_admin_client.get(f"/api/v1/lms/courses/{course_id}/")
    assert detail.data["lesson_count"] == 1
    assert len(detail.data["modules"]) == 1
    assert len(detail.data["modules"][0]["lessons"]) == 1


@pytest.mark.django_db
def test_lesson_filter_by_curriculum_code(platform_admin_client, tenant_id):
    c = platform_admin_client.post(
        "/api/v1/lms/courses/", {"name": "Maths", "subject": "Mathematics", "year_level": 8}, format="json"
    )
    m = platform_admin_client.post(
        "/api/v1/lms/modules/", {"course": c.data["id"], "name": "M1"}, format="json"
    )
    platform_admin_client.post(
        "/api/v1/lms/lessons/",
        {"module": m.data["id"], "title": "L1", "curriculum_code": "AC9M8N01"},
        format="json",
    )
    resp = platform_admin_client.get("/api/v1/lms/lessons/?curriculum_code=AC9M8N01")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert len(rows) == 1
