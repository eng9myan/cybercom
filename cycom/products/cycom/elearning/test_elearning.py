import uuid

import pytest
from rest_framework.test import APIClient

from platform.tenant.models import Tenant
from products.cycom.elearning.models import Course, Enrollment, Lesson, LessonProgress

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "instructor@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def tenant(tenant_id):
    obj, _ = Tenant.objects.update_or_create(
        id=tenant_id, defaults={"name": f"learn-{tenant_id}", "slug": f"learn-{str(tenant_id)[:8]}"}
    )
    return obj


@pytest.fixture
def public_client():
    return APIClient()


def test_public_list_only_shows_published_courses(public_client, tenant):
    Course.objects.create(tenant_id=tenant.id, title="Public Course", is_published=True)
    Course.objects.create(tenant_id=tenant.id, title="Draft Course", is_published=False)

    resp = public_client.get(f"/api/learn/{tenant.slug}/courses/")
    assert resp.status_code == 200
    titles = [c["title"] for c in resp.data]
    assert "Public Course" in titles
    assert "Draft Course" not in titles


def test_unpublished_course_detail_hidden(public_client, tenant):
    course = Course.objects.create(tenant_id=tenant.id, title="Secret Course", is_published=False)
    resp = public_client.get(f"/api/learn/{tenant.slug}/courses/{course.slug}/")
    assert resp.status_code == 400


def test_enroll_and_complete_lesson_tracks_progress(public_client, tenant):
    course = Course.objects.create(tenant_id=tenant.id, title="Onboarding", is_published=True)
    lesson1 = Lesson.objects.create(tenant_id=tenant.id, course=course, title="Intro", order=1)
    Lesson.objects.create(tenant_id=tenant.id, course=course, title="Advanced", order=2)

    resp = public_client.post(
        f"/api/learn/{tenant.slug}/courses/{course.slug}/enroll/", {"student_name": "Sam"}, format="json"
    )
    assert resp.status_code == 201
    token = resp.data["token"]

    resp = public_client.post(
        f"/api/learn/{tenant.slug}/courses/{course.slug}/lessons/{lesson1.slug}/progress/",
        {"token": token},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["completed"] is True
    assert resp.data["progress_percent"] == 50


def test_completing_lesson_twice_is_idempotent(public_client, tenant):
    course = Course.objects.create(tenant_id=tenant.id, title="Onboarding", is_published=True)
    lesson = Lesson.objects.create(tenant_id=tenant.id, course=course, title="Intro")
    enrollment = Enrollment.objects.create(tenant_id=tenant.id, course=course)

    for _ in range(2):
        public_client.post(
            f"/api/learn/{tenant.slug}/courses/{course.slug}/lessons/{lesson.slug}/progress/",
            {"token": enrollment.token},
            format="json",
        )
    assert LessonProgress.objects.filter(enrollment=enrollment, lesson=lesson).count() == 1


def test_progress_check_does_not_require_post(public_client, tenant):
    course = Course.objects.create(tenant_id=tenant.id, title="Onboarding", is_published=True)
    lesson = Lesson.objects.create(tenant_id=tenant.id, course=course, title="Intro")
    enrollment = Enrollment.objects.create(tenant_id=tenant.id, course=course)

    resp = public_client.get(
        f"/api/learn/{tenant.slug}/courses/{course.slug}/lessons/{lesson.slug}/progress/?token={enrollment.token}"
    )
    assert resp.status_code == 200
    assert resp.data["completed"] is False


def test_progress_rejects_foreign_enrollment_token(public_client, tenant):
    course_a = Course.objects.create(tenant_id=tenant.id, title="Course A", is_published=True)
    course_b = Course.objects.create(tenant_id=tenant.id, title="Course B", is_published=True)
    lesson_b = Lesson.objects.create(tenant_id=tenant.id, course=course_b, title="B Lesson")
    enrollment_a = Enrollment.objects.create(tenant_id=tenant.id, course=course_a)

    resp = public_client.post(
        f"/api/learn/{tenant.slug}/courses/{course_b.slug}/lessons/{lesson_b.slug}/progress/",
        {"token": enrollment_a.token},
        format="json",
    )
    assert resp.status_code == 400


def test_staff_publish_action(admin_client, tenant_id):
    course = Course.objects.create(tenant_id=tenant_id, title="Draft")
    resp = admin_client.post(f"/api/v1/elearning/courses/{course.id}/publish/")
    assert resp.status_code == 200
    assert resp.data["is_published"] is True


def test_staff_enrollment_report_shows_completion_count(admin_client, tenant_id):
    course = Course.objects.create(tenant_id=tenant_id, title="Onboarding")
    lesson = Lesson.objects.create(tenant_id=tenant_id, course=course, title="Intro")
    enrollment = Enrollment.objects.create(tenant_id=tenant_id, course=course, student_name="Sam")
    LessonProgress.objects.create(tenant_id=tenant_id, enrollment=enrollment, lesson=lesson)

    resp = admin_client.get("/api/v1/elearning/enrollments/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    row = next(r for r in rows if r["student_name"] == "Sam")
    assert row["completed_lesson_count"] == 1


def test_admin_crud_requires_auth(tenant_id):
    resp = APIClient().get("/api/v1/elearning/courses/")
    assert resp.status_code == 401
    resp = APIClient().get("/api/v1/elearning/enrollments/")
    assert resp.status_code == 401


def test_tenant_isolation_on_admin_course_list(admin_client, tenant_id):
    Course.objects.create(tenant_id=uuid.uuid4(), title="Foreign Course")
    resp = admin_client.get("/api/v1/elearning/courses/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["title"] != "Foreign Course" for r in rows)
