"""
Adversarial RBAC probes for the assessment app.

These deliberately try to BREAK the access rules rather than confirm them. The
scheduled adversarial-review agents never ran (the account hit its spend limit),
so this file is the independent check: every test here is an attack that must
fail. Assertions are made against the raw wire bytes where an answer key is at
stake, because a nested serializer can leak a field a queryset filter never sees.
"""

import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.assessment.models import Assignment, Choice, Question, Quiz, Submission
from products.cyed.sis.models import ClassSection, Guardian, Student

SECRET = "Pythagoras"  # the correct answer; must never reach a student pre-submission


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


@pytest.fixture
def world(tenant_id):
    """Two students, a guardian for one of them, a quiz with a known answer key."""
    section = ClassSection.objects.create(tenant_id=tenant_id, name="9A", year_level=9)
    alice = Student.objects.create(tenant_id=tenant_id, first_name="Alice", last_name="A",
                                   year_level=9, email="alice@stu.edu.au")
    bob = Student.objects.create(tenant_id=tenant_id, first_name="Bob", last_name="B",
                                 year_level=9, email="bob@stu.edu.au")
    guardian = Guardian.objects.create(tenant_id=tenant_id, first_name="Ann", last_name="A",
                                       email="parent-of-alice@home.com")
    guardian.students.add(alice)

    quiz = Quiz.objects.create(tenant_id=tenant_id, title="Geometry", class_section=section,
                               is_published=True)
    q = Question.objects.create(tenant_id=tenant_id, quiz=quiz, text="Whose theorem?",
                                kind="multiple_choice", points=1, sequence=1)
    Choice.objects.create(tenant_id=tenant_id, question=q, text=SECRET, is_correct=True, sequence=1)
    Choice.objects.create(tenant_id=tenant_id, question=q, text="Euclid", is_correct=False, sequence=2)

    assignment = Assignment.objects.create(tenant_id=tenant_id, title="Essay", class_section=section,
                                           max_score=10, is_published=True)
    bob_sub = Submission.objects.create(tenant_id=tenant_id, assignment=assignment, student=bob,
                                        text_response="Bob private work", status="submitted")
    return {"section": section, "alice": alice, "bob": bob, "quiz": quiz, "question": q,
            "assignment": assignment, "bob_sub": bob_sub}


def _body(resp):
    return resp.content.decode("utf-8", "replace")


# ── Control ──────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_control_student_reaches_endpoints_and_sees_own_work(client_for, world, tenant_id):
    """
    Guards every negative test below. Several of them assert "X is absent from
    the response" — which would pass trivially if students were simply locked out
    of the API. This proves they are not: a student gets 200 everywhere and can
    read their own submission, so the absence of other students' data in those
    tests is real scoping, not a blanket denial.
    """
    Submission.objects.create(tenant_id=tenant_id, assignment=world["assignment"],
                              student=world["alice"], text_response="ALICE_OWN_WORK",
                              status="submitted")
    stu = client_for(["student"], email="alice@stu.edu.au")
    for ep in ("submissions", "attempts", "answers", "assignments", "quizzes", "questions", "choices"):
        assert stu.get(f"/api/v1/assessment/{ep}/").status_code == 200, f"student locked out of {ep}"
    assert "ALICE_OWN_WORK" in _body(stu.get("/api/v1/assessment/submissions/"))


# ── Answer-key leakage ───────────────────────────────────────────────────────
@pytest.mark.django_db
def test_student_cannot_read_answer_key_from_choices_endpoint(client_for, world):
    stu = client_for(["student"], email="alice@stu.edu.au")
    resp = stu.get("/api/v1/assessment/choices/")
    assert "is_correct" not in _body(resp), "answer key leaked via /choices/"


@pytest.mark.django_db
def test_student_cannot_read_answer_key_from_questions_endpoint(client_for, world):
    stu = client_for(["student"], email="alice@stu.edu.au")
    resp = stu.get("/api/v1/assessment/questions/")
    assert "is_correct" not in _body(resp), "answer key leaked via nested choices on /questions/"
    assert "accepted_answers" not in _body(resp)


@pytest.mark.django_db
def test_student_cannot_read_answer_key_from_quiz_detail(client_for, world):
    stu = client_for(["student"], email="alice@stu.edu.au")
    resp = stu.get(f"/api/v1/assessment/quizzes/{world['quiz'].id}/")
    assert "is_correct" not in _body(resp), "answer key leaked via quiz detail"


@pytest.mark.django_db
def test_staff_can_still_see_the_answer_key(client_for, world):
    """The guard must not be so blunt that teachers lose the key."""
    teacher = client_for(["teacher"], email="t@cyed.edu.au")
    resp = teacher.get("/api/v1/assessment/choices/")
    assert "is_correct" in _body(resp), "teachers must be able to see the key"


# ── Cross-student data access ────────────────────────────────────────────────
@pytest.mark.django_db
def test_student_cannot_list_another_students_submission(client_for, world):
    alice = client_for(["student"], email="alice@stu.edu.au")
    resp = alice.get("/api/v1/assessment/submissions/")
    assert "Bob private work" not in _body(resp), "cross-student submission leak on list"


@pytest.mark.django_db
def test_student_cannot_fetch_another_students_submission_by_id(client_for, world):
    alice = client_for(["student"], email="alice@stu.edu.au")
    resp = alice.get(f"/api/v1/assessment/submissions/{world['bob_sub'].id}/")
    assert resp.status_code in (403, 404), f"direct-id access allowed: {resp.status_code}"
    assert "Bob private work" not in _body(resp)


@pytest.mark.django_db
def test_student_cannot_read_another_students_answers(client_for, world):
    alice = client_for(["student"], email="alice@stu.edu.au")
    resp = alice.get("/api/v1/assessment/answers/")
    assert resp.status_code in (200, 403)
    if resp.status_code == 200:
        body = _body(resp)
        assert "Bob" not in body


@pytest.mark.django_db
def test_student_cannot_list_another_students_attempts(client_for, world):
    from products.cyed.assessment.models import QuizAttempt

    QuizAttempt.objects.create(tenant_id=world["bob"].tenant_id, quiz=world["quiz"],
                               student=world["bob"], attempt_number=1)
    alice = client_for(["student"], email="alice@stu.edu.au")
    resp = alice.get("/api/v1/assessment/attempts/")
    if resp.status_code == 200:
        data = resp.json()
        rows = data["results"] if isinstance(data, dict) else data
        assert all(str(r.get("student")) != str(world["bob"].id) for r in rows), \
            "student can see another student's quiz attempts"


# ── Parent scope ─────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_parent_cannot_read_a_child_who_is_not_theirs(client_for, world):
    parent = client_for(["parent"], email="parent-of-alice@home.com")
    resp = parent.get("/api/v1/assessment/submissions/")
    assert "Bob private work" not in _body(resp), "parent reached a non-child submission"


@pytest.mark.django_db
def test_unrelated_parent_sees_nothing(client_for, world):
    stranger = client_for(["parent"], email="nobody@home.com")
    resp = stranger.get("/api/v1/assessment/submissions/")
    if resp.status_code == 200:
        data = resp.json()
        rows = data["results"] if isinstance(data, dict) else data
        assert rows == [], "an unrelated parent received submissions"


# ── Privilege escalation ─────────────────────────────────────────────────────
@pytest.mark.django_db
def test_student_cannot_author_an_assignment(client_for, world):
    stu = client_for(["student"], email="alice@stu.edu.au")
    resp = stu.post("/api/v1/assessment/assignments/",
                    {"title": "Fake", "class_section": str(world["section"].id), "max_score": 10},
                    format="json")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_student_cannot_create_a_choice_marked_correct(client_for, world):
    stu = client_for(["student"], email="alice@stu.edu.au")
    resp = stu.post("/api/v1/assessment/choices/",
                    {"question": str(world["question"].id), "text": "mine", "is_correct": True},
                    format="json")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_student_cannot_grade_their_own_submission(client_for, world):
    """Marks must only ever be written through the staff-only grade action."""
    alice_sub = Submission.objects.create(
        tenant_id=world["alice"].tenant_id, assignment=world["assignment"],
        student=world["alice"], text_response="mine", status="submitted",
    )
    stu = client_for(["student"], email="alice@stu.edu.au")
    resp = stu.patch(f"/api/v1/assessment/submissions/{alice_sub.id}/",
                     {"score": 10, "status": "graded"}, format="json")
    alice_sub.refresh_from_db()
    assert alice_sub.score in (None, 0), f"student wrote their own mark: {alice_sub.score}"

    direct = stu.post(f"/api/v1/assessment/submissions/{alice_sub.id}/grade/",
                      {"score": 10}, format="json")
    assert direct.status_code == 403


# ── Tenant isolation ─────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_other_tenant_cannot_see_this_tenants_quizzes(mint_token, mock_jwks, world):
    other_tenant = uuid.uuid4()
    token = mint_token({"sub": str(uuid.uuid4()), "email": "t@other.edu.au",
                        "tenant_id": str(other_tenant), "realm_access": {"roles": ["teacher"]}})
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    resp = c.get("/api/v1/assessment/quizzes/")
    if resp.status_code == 200:
        body = _body(resp)
        assert "Geometry" not in body, "cross-tenant quiz leak"
