"""
Tests for the assignment-submission + quiz engine.

Coverage map:
  * assignment authoring, publishing and visibility;
  * submission happy path, late refusal AND late acceptance, resubmission;
  * the gradebook.Grade write-back (the reason this app links to gradebook);
  * quiz authoring, max_attempts, auto-marking of every kind, partial credit,
    essays left for a human;
  * every RBAC boundary — especially that a learner cannot read the answer key
    before submitting, and cannot read another learner's work.
"""

import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.assessment import services
from products.cyed.assessment.models import (
    Answer,
    Assignment,
    Choice,
    Question,
    Quiz,
    QuizAttempt,
    Submission,
)
from products.cyed.gradebook.models import Assessment as GradebookAssessment
from products.cyed.gradebook.models import Grade
from products.cyed.sis.models import ClassSection, Enrolment, Guardian, Student

STUDENT_EMAIL = "ivy.chen@student.cyed.edu.au"
OTHER_EMAIL = "raj.patel@student.cyed.edu.au"
PARENT_EMAIL = "mei.chen@families.cyed.edu.au"
TEACHER_EMAIL = "teacher@cyed.edu.au"

BASE = "/api/v1/assessment"


# ══════════════════════════ fixtures ══════════════════════════
@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token(
            {
                "sub": str(uuid.uuid4()),
                "email": email,
                "tenant_id": str(tenant_id),
                "realm_access": {"roles": roles},
            }
        )
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c

    return _make


@pytest.fixture
def section(tenant_id):
    return ClassSection.objects.create(
        tenant_id=tenant_id, name="8A Mathematics", subject="Mathematics", year_level=8
    )


@pytest.fixture
def student(tenant_id, section):
    s = Student.objects.create(
        tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8, email=STUDENT_EMAIL
    )
    Enrolment.objects.create(tenant_id=tenant_id, student=s, class_section=section, status="active")
    return s


@pytest.fixture
def other_student(tenant_id, section):
    s = Student.objects.create(
        tenant_id=tenant_id, first_name="Raj", last_name="Patel", year_level=8, email=OTHER_EMAIL
    )
    Enrolment.objects.create(tenant_id=tenant_id, student=s, class_section=section, status="active")
    return s


@pytest.fixture
def guardian(tenant_id, student):
    g = Guardian.objects.create(
        tenant_id=tenant_id, first_name="Mei", last_name="Chen",
        relationship="mother", email=PARENT_EMAIL,
    )
    g.students.add(student)
    return g


@pytest.fixture
def teacher(client_for):
    return client_for(["teacher"], email=TEACHER_EMAIL)


@pytest.fixture
def principal(client_for):
    return client_for(["principal"], email="head@cyed.edu.au")


@pytest.fixture
def learner(client_for, student):
    return client_for(["student"], email=STUDENT_EMAIL)


@pytest.fixture
def other_learner(client_for, other_student):
    return client_for(["student"], email=OTHER_EMAIL)


@pytest.fixture
def parent(client_for, guardian):
    return client_for(["parent"], email=PARENT_EMAIL)


@pytest.fixture
def assignment(tenant_id, section):
    return Assignment.objects.create(
        tenant_id=tenant_id, class_section=section, title="Fractions Investigation",
        instructions="Show your working.", max_score=Decimal("20"), is_published=True,
        curriculum_code="AC9M8N01",
    )


@pytest.fixture
def quiz_bundle(tenant_id, section):
    """One quiz exercising every question kind. Total 13 points."""
    quiz = Quiz.objects.create(
        tenant_id=tenant_id, class_section=section, title="Number & Algebra Check",
        max_attempts=2, is_published=True, curriculum_code="AC9M8N01",
    )
    mc = Question.objects.create(
        tenant_id=tenant_id, quiz=quiz, text="What is 2 + 2?",
        kind="multiple_choice", points=Decimal("2"), sequence=1,
    )
    mc_right = Choice.objects.create(tenant_id=tenant_id, question=mc, text="4", is_correct=True, sequence=1)
    mc_wrong = Choice.objects.create(tenant_id=tenant_id, question=mc, text="5", sequence=2)

    tf = Question.objects.create(
        tenant_id=tenant_id, quiz=quiz, text="7 is prime.",
        kind="true_false", points=Decimal("1"), sequence=2,
    )
    tf_true = Choice.objects.create(tenant_id=tenant_id, question=tf, text="True", is_correct=True, sequence=1)
    tf_false = Choice.objects.create(tenant_id=tenant_id, question=tf, text="False", sequence=2)

    sa = Question.objects.create(
        tenant_id=tenant_id, quiz=quiz, text="Name the theorem relating a right triangle's sides.",
        kind="short_answer", points=Decimal("1"), sequence=3,
        accepted_answers=["Pythagoras", "Pythagorean theorem"],
    )

    ms = Question.objects.create(
        tenant_id=tenant_id, quiz=quiz, text="Which of these are prime?",
        kind="multi_select", points=Decimal("4"), sequence=4,
    )
    ms_a = Choice.objects.create(tenant_id=tenant_id, question=ms, text="3", is_correct=True, sequence=1)
    ms_b = Choice.objects.create(tenant_id=tenant_id, question=ms, text="5", is_correct=True, sequence=2)
    ms_c = Choice.objects.create(tenant_id=tenant_id, question=ms, text="9", sequence=3)
    ms_d = Choice.objects.create(tenant_id=tenant_id, question=ms, text="12", sequence=4)

    essay = Question.objects.create(
        tenant_id=tenant_id, quiz=quiz, text="Explain why 1 is not prime.",
        kind="essay", points=Decimal("5"), sequence=5,
    )
    return {
        "quiz": quiz, "mc": mc, "mc_right": mc_right, "mc_wrong": mc_wrong,
        "tf": tf, "tf_true": tf_true, "tf_false": tf_false, "sa": sa,
        "ms": ms, "ms_a": ms_a, "ms_b": ms_b, "ms_c": ms_c, "ms_d": ms_d,
        "essay": essay,
    }


def rows_of(response):
    data = response.data
    return data["results"] if isinstance(data, dict) and "results" in data else data


# ══════════════════════════ assignments ══════════════════════════
@pytest.mark.django_db
def test_teacher_authors_and_publishes_assignment(teacher, learner, tenant_id, section):
    created = teacher.post(
        f"{BASE}/assignments/",
        {
            "class_section": str(section.id), "title": "Algebra Task",
            "instructions": "Solve for x.", "max_score": "25",
            "curriculum_code": "AC9M8A01", "allow_late": True,
        },
        format="json",
    )
    assert created.status_code == 201, created.data
    assert created.data["is_published"] is False
    assignment_id = created.data["id"]

    # Unpublished work is invisible to the learner...
    assert len(rows_of(learner.get(f"{BASE}/assignments/"))) == 0

    published = teacher.post(f"{BASE}/assignments/{assignment_id}/publish/")
    assert published.status_code == 200
    assert published.data["is_published"] is True

    # ...and visible once published.
    visible = rows_of(learner.get(f"{BASE}/assignments/"))
    assert [r["title"] for r in visible] == ["Algebra Task"]


@pytest.mark.django_db
def test_student_cannot_author_or_publish_assignment(learner, tenant_id, section, assignment):
    denied = learner.post(
        f"{BASE}/assignments/",
        {"class_section": str(section.id), "title": "Homework I set myself"},
        format="json",
    )
    assert denied.status_code == 403
    assert learner.post(f"{BASE}/assignments/{assignment.id}/publish/").status_code == 403
    assert learner.patch(
        f"{BASE}/assignments/{assignment.id}/", {"is_published": False}, format="json"
    ).status_code == 403


@pytest.mark.django_db
def test_assignment_rejects_zero_max_score(teacher, section):
    bad = teacher.post(
        f"{BASE}/assignments/",
        {"class_section": str(section.id), "title": "Broken", "max_score": "0"},
        format="json",
    )
    assert bad.status_code == 400
    assert "max_score" in bad.data["detail"]


@pytest.mark.django_db
def test_assignment_gradebook_link_must_match_class_section(teacher, tenant_id, section):
    elsewhere = ClassSection.objects.create(tenant_id=tenant_id, name="9B Science", year_level=9)
    foreign = GradebookAssessment.objects.create(
        tenant_id=tenant_id, class_section=elsewhere, name="Science Prac"
    )
    bad = teacher.post(
        f"{BASE}/assignments/",
        {"class_section": str(section.id), "title": "Mismatched", "assessment": str(foreign.id)},
        format="json",
    )
    assert bad.status_code == 400
    assert "different class section" in bad.data["detail"]


@pytest.mark.django_db
def test_assignment_tenant_isolation(teacher, tenant_id):
    other_tenant = uuid.uuid4()
    foreign_section = ClassSection.objects.create(tenant_id=other_tenant, name="Foreign", year_level=8)
    Assignment.objects.create(
        tenant_id=other_tenant, class_section=foreign_section, title="Foreign Task", is_published=True
    )
    titles = [r["title"] for r in rows_of(teacher.get(f"{BASE}/assignments/"))]
    assert "Foreign Task" not in titles


# ══════════════════════════ submissions ══════════════════════════
@pytest.mark.django_db
def test_student_submits_own_work(learner, tenant_id, assignment, student):
    draft = learner.post(
        f"{BASE}/submissions/",
        {"assignment": str(assignment.id), "student": str(student.id), "text_response": "Draft"},
        format="json",
    )
    assert draft.status_code == 201, draft.data
    assert draft.data["status"] == "draft"
    assert draft.data["submitted_at"] is None

    handed_in = learner.post(
        f"{BASE}/submissions/{draft.data['id']}/submit/",
        {"text_response": "My finished working."},
        format="json",
    )
    assert handed_in.status_code == 200, handed_in.data
    assert handed_in.data["status"] == "submitted"
    assert handed_in.data["submitted_at"] is not None
    assert handed_in.data["is_handed_in"] is True


@pytest.mark.django_db
def test_late_submission_refused_when_late_not_allowed(learner, tenant_id, section, student):
    overdue = Assignment.objects.create(
        tenant_id=tenant_id, class_section=section, title="Closed Task",
        due_at=timezone.now() - timedelta(hours=2), allow_late=False, is_published=True,
    )
    assert overdue.is_overdue is True

    draft = learner.post(
        f"{BASE}/submissions/",
        {"assignment": str(overdue.id), "student": str(student.id), "text_response": "Late work"},
        format="json",
    )
    assert draft.status_code == 201, draft.data

    refused = learner.post(f"{BASE}/submissions/{draft.data['id']}/submit/")
    assert refused.status_code == 400
    assert "late" in refused.data["detail"].lower()
    assert Submission.objects.get(id=draft.data["id"]).status == "draft"


@pytest.mark.django_db
def test_late_submission_accepted_and_flagged_when_allowed(learner, tenant_id, section, student):
    overdue = Assignment.objects.create(
        tenant_id=tenant_id, class_section=section, title="Open Task",
        due_at=timezone.now() - timedelta(hours=2), allow_late=True, is_published=True,
    )
    draft = learner.post(
        f"{BASE}/submissions/",
        {"assignment": str(overdue.id), "student": str(student.id), "text_response": "Better late"},
        format="json",
    )
    accepted = learner.post(f"{BASE}/submissions/{draft.data['id']}/submit/")
    assert accepted.status_code == 200, accepted.data
    assert accepted.data["status"] == "late"
    assert accepted.data["submitted_at"] is not None


@pytest.mark.django_db
def test_posting_submitted_status_past_deadline_is_refused(learner, tenant_id, section, student):
    """The late rule cannot be dodged by creating the row already 'submitted'."""
    overdue = Assignment.objects.create(
        tenant_id=tenant_id, class_section=section, title="Closed Task",
        due_at=timezone.now() - timedelta(days=1), allow_late=False, is_published=True,
    )
    sneaky = learner.post(
        f"{BASE}/submissions/",
        {"assignment": str(overdue.id), "student": str(student.id), "status": "submitted"},
        format="json",
    )
    assert sneaky.status_code == 400
    assert Submission.objects.count() == 0


@pytest.mark.django_db
def test_duplicate_submission_is_a_clean_400(learner, tenant_id, assignment, student):
    payload = {"assignment": str(assignment.id), "student": str(student.id)}
    assert learner.post(f"{BASE}/submissions/", payload, format="json").status_code == 201
    clash = learner.post(f"{BASE}/submissions/", payload, format="json")
    assert clash.status_code == 400  # not a 500 IntegrityError
    assert "attempt_number" in clash.data["detail"]

    # A second attempt with an incremented number is fine.
    retry = learner.post(
        f"{BASE}/submissions/", {**payload, "attempt_number": 2}, format="json"
    )
    assert retry.status_code == 201, retry.data


@pytest.mark.django_db
def test_student_cannot_submit_under_another_students_name(learner, assignment, student, other_student):
    impersonation = learner.post(
        f"{BASE}/submissions/",
        {"assignment": str(assignment.id), "student": str(other_student.id), "text_response": "x"},
        format="json",
    )
    assert impersonation.status_code == 403
    assert Submission.objects.count() == 0


@pytest.mark.django_db
def test_student_cannot_read_another_students_submission(
    learner, other_learner, tenant_id, assignment, student, other_student
):
    mine = Submission.objects.create(
        tenant_id=tenant_id, assignment=assignment, student=student, text_response="mine"
    )
    theirs = Submission.objects.create(
        tenant_id=tenant_id, assignment=assignment, student=other_student, text_response="theirs"
    )

    listed = rows_of(learner.get(f"{BASE}/submissions/"))
    assert [r["id"] for r in listed] == [str(mine.id)]
    assert learner.get(f"{BASE}/submissions/{theirs.id}/").status_code == 404
    # Nor by asking for them explicitly.
    filtered = rows_of(learner.get(f"{BASE}/submissions/?student={other_student.id}"))
    assert filtered == []


@pytest.mark.django_db
def test_student_cannot_edit_work_after_handing_it_in(learner, tenant_id, assignment, student):
    sub = Submission.objects.create(
        tenant_id=tenant_id, assignment=assignment, student=student,
        status="submitted", submitted_at=timezone.now(),
    )
    blocked = learner.patch(
        f"{BASE}/submissions/{sub.id}/", {"text_response": "sneaky rewrite"}, format="json"
    )
    assert blocked.status_code == 403


@pytest.mark.django_db
def test_parent_reads_own_child_only_and_cannot_write(
    parent, tenant_id, assignment, student, other_student
):
    mine = Submission.objects.create(
        tenant_id=tenant_id, assignment=assignment, student=student, text_response="child's work"
    )
    Submission.objects.create(
        tenant_id=tenant_id, assignment=assignment, student=other_student, text_response="not theirs"
    )

    listed = rows_of(parent.get(f"{BASE}/submissions/"))
    assert [r["id"] for r in listed] == [str(mine.id)]

    denied = parent.post(
        f"{BASE}/submissions/",
        {"assignment": str(assignment.id), "student": str(student.id)},
        format="json",
    )
    assert denied.status_code == 403
    assert parent.post(f"{BASE}/submissions/{mine.id}/submit/").status_code == 403
    assert parent.post(
        f"{BASE}/submissions/{mine.id}/grade/", {"score": "20"}, format="json"
    ).status_code == 403


@pytest.mark.django_db
def test_teacher_sees_every_submission_for_an_assignment(
    teacher, learner, tenant_id, assignment, student, other_student
):
    Submission.objects.create(
        tenant_id=tenant_id, assignment=assignment, student=student,
        status="submitted", submitted_at=timezone.now(),
    )
    Submission.objects.create(tenant_id=tenant_id, assignment=assignment, student=other_student)

    view = teacher.get(f"{BASE}/assignments/{assignment.id}/submissions/")
    assert view.status_code == 200
    assert view.data["count"] == 2
    assert view.data["handed_in"] == 1
    assert {r["student_name"] for r in view.data["results"]} == {"Ivy Chen", "Raj Patel"}

    # The marking view is staff-only.
    assert learner.get(f"{BASE}/assignments/{assignment.id}/submissions/").status_code == 403


@pytest.mark.django_db
def test_submission_file_upload_and_download(learner, tenant_id, assignment, student):
    from django.core.files.uploadedfile import SimpleUploadedFile

    upload = SimpleUploadedFile("working.txt", b"my working out", content_type="text/plain")
    created = learner.post(
        f"{BASE}/submissions/",
        {"assignment": str(assignment.id), "student": str(student.id), "file": upload},
        format="multipart",
    )
    assert created.status_code == 201, created.data
    assert created.data["has_file"] is True
    assert created.data["file_name"] == "working.txt"
    assert "file_bytes" not in created.data  # raw bytes never serialised

    download = learner.get(f"{BASE}/submissions/{created.data['id']}/file/")
    assert download.status_code == 200
    assert download.content == b"my working out"


@pytest.mark.django_db
def test_my_assignments_shows_outstanding_and_submitted(
    learner, tenant_id, section, student, assignment
):
    done = Assignment.objects.create(
        tenant_id=tenant_id, class_section=section, title="Already Done",
        max_score=Decimal("10"), is_published=True,
    )
    Assignment.objects.create(
        tenant_id=tenant_id, class_section=section, title="Hidden Draft", is_published=False
    )
    Submission.objects.create(
        tenant_id=tenant_id, assignment=done, student=student,
        status="submitted", submitted_at=timezone.now(),
    )

    mine = learner.get(f"{BASE}/assignments/mine/")
    assert mine.status_code == 200
    by_title = {r["title"]: r for r in mine.data["results"]}
    assert set(by_title) == {"Fractions Investigation", "Already Done"}  # unpublished excluded
    assert by_title["Fractions Investigation"]["status"] == "outstanding"
    assert by_title["Already Done"]["status"] == "submitted"
    assert mine.data["outstanding"] == 1


@pytest.mark.django_db
def test_my_assignments_requires_a_named_student_for_staff(teacher, student, assignment):
    assert teacher.get(f"{BASE}/assignments/mine/").status_code == 400
    named = teacher.get(f"{BASE}/assignments/mine/?student={student.id}")
    assert named.status_code == 200
    assert named.data["count"] == 1


@pytest.mark.django_db
def test_parent_my_assignments_covers_their_child(parent, student, assignment):
    view = parent.get(f"{BASE}/assignments/mine/")
    assert view.status_code == 200
    assert view.data["count"] == 1
    assert view.data["results"][0]["student"] == str(student.id)


# ══════════════════════════ grading → gradebook ══════════════════════════
@pytest.mark.django_db
def test_grading_a_submission_writes_the_gradebook_grade(
    teacher, tenant_id, section, student
):
    """The whole point of Assignment.assessment: marking here lands in gradebook."""
    gb_assessment = GradebookAssessment.objects.create(
        tenant_id=tenant_id, class_section=section, name="Fractions Investigation",
        assessment_type="assignment", max_score=Decimal("20"), curriculum_code="AC9M8N01",
    )
    linked = Assignment.objects.create(
        tenant_id=tenant_id, class_section=section, assessment=gb_assessment,
        title="Fractions Investigation", max_score=Decimal("20"), is_published=True,
    )
    sub = Submission.objects.create(
        tenant_id=tenant_id, assignment=linked, student=student,
        status="submitted", submitted_at=timezone.now(),
    )
    assert Grade.objects.count() == 0

    marked = teacher.post(
        f"{BASE}/submissions/{sub.id}/grade/",
        {"score": "18", "feedback": "Excellent reasoning."},
        format="json",
    )
    assert marked.status_code == 200, marked.data
    assert marked.data["status"] == "graded"
    assert marked.data["percentage"] == 90.0
    assert marked.data["graded_by"] == TEACHER_EMAIL
    assert marked.data["gradebook_grade"] is not None

    grade = Grade.objects.get(assessment=gb_assessment, student=student)
    assert grade.score == Decimal("18.00")
    assert grade.comment == "Excellent reasoning."
    assert grade.achievement_level == "A"
    assert str(grade.id) == marked.data["gradebook_grade"]


@pytest.mark.django_db
def test_regrading_updates_the_same_gradebook_row(teacher, tenant_id, section, student):
    gb_assessment = GradebookAssessment.objects.create(
        tenant_id=tenant_id, class_section=section, name="Task", max_score=Decimal("20")
    )
    linked = Assignment.objects.create(
        tenant_id=tenant_id, class_section=section, assessment=gb_assessment,
        title="Task", max_score=Decimal("20"), is_published=True,
    )
    sub = Submission.objects.create(
        tenant_id=tenant_id, assignment=linked, student=student, status="submitted"
    )
    teacher.post(f"{BASE}/submissions/{sub.id}/grade/", {"score": "18"}, format="json")
    teacher.post(
        f"{BASE}/submissions/{sub.id}/grade/",
        {"score": "11", "feedback": "Remarked after moderation."},
        format="json",
    )
    assert Grade.objects.count() == 1
    grade = Grade.objects.get()
    assert grade.score == Decimal("11.00")
    assert grade.achievement_level == "C"  # 55%


@pytest.mark.django_db
def test_grading_an_unlinked_assignment_writes_no_gradebook_row(
    teacher, tenant_id, assignment, student
):
    sub = Submission.objects.create(
        tenant_id=tenant_id, assignment=assignment, student=student, status="submitted"
    )
    marked = teacher.post(f"{BASE}/submissions/{sub.id}/grade/", {"score": "15"}, format="json")
    assert marked.status_code == 200
    assert marked.data["gradebook_grade"] is None
    assert Grade.objects.count() == 0


@pytest.mark.django_db
def test_students_and_parents_cannot_grade(learner, parent, tenant_id, assignment, student):
    sub = Submission.objects.create(
        tenant_id=tenant_id, assignment=assignment, student=student, status="submitted"
    )
    assert learner.post(
        f"{BASE}/submissions/{sub.id}/grade/", {"score": "20"}, format="json"
    ).status_code == 403
    assert parent.post(
        f"{BASE}/submissions/{sub.id}/grade/", {"score": "20"}, format="json"
    ).status_code == 403
    sub.refresh_from_db()
    assert sub.score is None


@pytest.mark.django_db
def test_students_cannot_write_their_own_score_through_the_serializer(
    learner, tenant_id, assignment, student
):
    created = learner.post(
        f"{BASE}/submissions/",
        {"assignment": str(assignment.id), "student": str(student.id), "score": "20",
         "feedback": "A+ from me"},
        format="json",
    )
    assert created.status_code == 201
    assert created.data["score"] is None
    assert created.data["feedback"] == ""


@pytest.mark.django_db
def test_score_outside_range_is_rejected(teacher, tenant_id, assignment, student):
    sub = Submission.objects.create(
        tenant_id=tenant_id, assignment=assignment, student=student, status="submitted"
    )
    too_high = teacher.post(f"{BASE}/submissions/{sub.id}/grade/", {"score": "21"}, format="json")
    assert too_high.status_code == 400
    assert "cannot exceed" in too_high.data["detail"]

    negative = teacher.post(f"{BASE}/submissions/{sub.id}/grade/", {"score": "-1"}, format="json")
    assert negative.status_code == 400


@pytest.mark.django_db
def test_return_requires_a_mark_first(teacher, tenant_id, assignment, student):
    sub = Submission.objects.create(
        tenant_id=tenant_id, assignment=assignment, student=student, status="submitted"
    )
    assert teacher.post(f"{BASE}/submissions/{sub.id}/return/").status_code == 400
    teacher.post(f"{BASE}/submissions/{sub.id}/grade/", {"score": "12"}, format="json")
    returned = teacher.post(f"{BASE}/submissions/{sub.id}/return/")
    assert returned.status_code == 200
    assert returned.data["status"] == "returned"


# ══════════════════════════ quiz authoring & the answer key ══════════════════════════
@pytest.mark.django_db
def test_teacher_builds_and_publishes_a_quiz(teacher, tenant_id, section):
    quiz = teacher.post(
        f"{BASE}/quizzes/",
        {"class_section": str(section.id), "title": "Primes", "time_limit_minutes": 20,
         "max_attempts": 2, "curriculum_code": "AC9M8N01"},
        format="json",
    )
    assert quiz.status_code == 201, quiz.data
    quiz_id = quiz.data["id"]

    # Publishing an empty quiz is refused.
    empty = teacher.post(f"{BASE}/quizzes/{quiz_id}/publish/")
    assert empty.status_code == 400

    question = teacher.post(
        f"{BASE}/questions/",
        {"quiz": quiz_id, "text": "Is 9 prime?", "kind": "true_false", "points": "1", "sequence": 1},
        format="json",
    )
    assert question.status_code == 201, question.data
    for text, correct in [("True", False), ("False", True)]:
        c = teacher.post(
            f"{BASE}/choices/",
            {"question": question.data["id"], "text": text, "is_correct": correct},
            format="json",
        )
        assert c.status_code == 201, c.data

    published = teacher.post(f"{BASE}/quizzes/{quiz_id}/publish/")
    assert published.status_code == 200
    assert published.data["is_published"] is True
    assert published.data["question_count"] == 1
    assert published.data["total_points"] == "1.00"


@pytest.mark.django_db
def test_short_answer_question_requires_an_answer_key(teacher, tenant_id, quiz_bundle):
    bad = teacher.post(
        f"{BASE}/questions/",
        {"quiz": str(quiz_bundle["quiz"].id), "text": "Define a factor.", "kind": "short_answer"},
        format="json",
    )
    assert bad.status_code == 400
    assert "accepted_answers" in bad.data["detail"]


@pytest.mark.django_db
def test_quiz_rejects_invalid_limits(teacher, section):
    bad = teacher.post(
        f"{BASE}/quizzes/",
        {"class_section": str(section.id), "title": "Broken", "max_attempts": 0},
        format="json",
    )
    assert bad.status_code == 400
    assert "max_attempts" in bad.data["detail"]


@pytest.mark.django_db
def test_student_never_receives_the_answer_key_before_submitting(learner, teacher, quiz_bundle):
    """The single most important guard in this app."""
    quiz = quiz_bundle["quiz"]

    detail = learner.get(f"{BASE}/quizzes/{quiz.id}/")
    assert detail.status_code == 200
    body = detail.content.decode()
    assert "is_correct" not in body
    assert "accepted_answers" not in body
    assert "Pythagoras" not in body  # the short-answer key itself

    questions = learner.get(f"{BASE}/questions/?quiz={quiz.id}")
    qbody = questions.content.decode()
    assert "accepted_answers" not in qbody
    assert "Pythagorean" not in qbody

    choices = learner.get(f"{BASE}/choices/?question={quiz_bundle['mc'].id}")
    assert choices.status_code == 200
    assert "is_correct" not in choices.content.decode()
    assert len(rows_of(choices)) == 2  # they can see the options, just not which is right

    # The teacher, by contrast, gets the full key.
    staff_view = teacher.get(f"{BASE}/quizzes/{quiz.id}/")
    staff_body = staff_view.content.decode()
    assert "is_correct" in staff_body
    assert "accepted_answers" in staff_body
    assert "Pythagoras" in staff_body


@pytest.mark.django_db
def test_shuffling_reorders_without_losing_or_leaking_questions(learner, teacher, quiz_bundle):
    quiz = quiz_bundle["quiz"]
    quiz.shuffle_questions = True
    quiz.save(update_fields=["shuffle_questions"])
    expected = {str(q.id) for q in quiz.questions.all()}

    sat = learner.post(f"{BASE}/quizzes/{quiz.id}/start/", {}, format="json")
    assert sat.status_code == 201
    assert {str(q["id"]) for q in sat.data["quiz"]["questions"]} == expected
    assert "is_correct" not in sat.content.decode()

    # Staff always get the authored order for editing.
    staff_view = teacher.get(f"{BASE}/quizzes/{quiz.id}/")
    assert [q["sequence"] for q in staff_view.data["questions"]] == [1, 2, 3, 4, 5]


@pytest.mark.django_db
def test_student_cannot_see_an_unpublished_quiz(learner, tenant_id, section):
    hidden = Quiz.objects.create(
        tenant_id=tenant_id, class_section=section, title="Draft Quiz", is_published=False
    )
    Question.objects.create(tenant_id=tenant_id, quiz=hidden, text="?", kind="essay")
    assert len(rows_of(learner.get(f"{BASE}/quizzes/"))) == 0
    assert learner.get(f"{BASE}/quizzes/{hidden.id}/").status_code == 404
    assert learner.post(f"{BASE}/quizzes/{hidden.id}/start/").status_code == 404
    assert len(rows_of(learner.get(f"{BASE}/questions/?quiz={hidden.id}"))) == 0


@pytest.mark.django_db
def test_student_cannot_see_a_quiz_for_a_class_they_are_not_in(learner, tenant_id):
    elsewhere = ClassSection.objects.create(tenant_id=tenant_id, name="9B Science", year_level=9)
    Quiz.objects.create(
        tenant_id=tenant_id, class_section=elsewhere, title="Not My Class", is_published=True
    )
    assert len(rows_of(learner.get(f"{BASE}/quizzes/"))) == 0


@pytest.mark.django_db
def test_student_cannot_author_quiz_content(learner, quiz_bundle, section):
    assert learner.post(
        f"{BASE}/quizzes/", {"class_section": str(section.id), "title": "Mine"}, format="json"
    ).status_code == 403
    assert learner.post(
        f"{BASE}/questions/",
        {"quiz": str(quiz_bundle["quiz"].id), "text": "?", "kind": "essay"},
        format="json",
    ).status_code == 403
    assert learner.patch(
        f"{BASE}/choices/{quiz_bundle['mc_wrong'].id}/", {"is_correct": True}, format="json"
    ).status_code == 403
    assert learner.post(f"{BASE}/quizzes/{quiz_bundle['quiz'].id}/publish/").status_code == 403


# ══════════════════════════ attempts & auto-marking ══════════════════════════
def _start(client, quiz):
    started = client.post(f"{BASE}/quizzes/{quiz.id}/start/", {}, format="json")
    assert started.status_code == 201, started.data
    return started


@pytest.mark.django_db
def test_max_attempts_is_enforced(learner, quiz_bundle):
    quiz = quiz_bundle["quiz"]  # max_attempts = 2
    first = _start(learner, quiz)
    second = _start(learner, quiz)
    assert first.data["attempt"]["attempt_number"] == 1
    assert second.data["attempt"]["attempt_number"] == 2

    third = learner.post(f"{BASE}/quizzes/{quiz.id}/start/", {}, format="json")
    assert third.status_code == 400
    assert "attempt" in third.data["detail"].lower()
    assert QuizAttempt.objects.count() == 2


@pytest.mark.django_db
def test_auto_marking_covers_every_kind_and_leaves_essays_for_a_human(
    learner, teacher, quiz_bundle, student
):
    quiz = quiz_bundle["quiz"]
    started = _start(learner, quiz)
    attempt_id = started.data["attempt"]["id"]
    assert started.data["attempt"]["max_score"] == "13.00"

    result = learner.post(
        f"{BASE}/attempts/{attempt_id}/submit/",
        {
            "answers": [
                {"question": str(quiz_bundle["mc"].id), "choices": [str(quiz_bundle["mc_right"].id)]},
                {"question": str(quiz_bundle["tf"].id), "choices": [str(quiz_bundle["tf_true"].id)]},
                # Deliberately messy casing/whitespace — must still match.
                {"question": str(quiz_bundle["sa"].id), "text_answer": "   PYTHAGORAS  "},
                # One of two correct options → half of 4 points.
                {"question": str(quiz_bundle["ms"].id), "choices": [str(quiz_bundle["ms_a"].id)]},
                {"question": str(quiz_bundle["essay"].id), "text_answer": "It has only one factor."},
            ]
        },
        format="json",
    )
    assert result.status_code == 200, result.data
    by_kind = {row["kind"]: row for row in result.data["questions"]}

    assert by_kind["multiple_choice"]["awarded"] == "2.00"
    assert by_kind["multiple_choice"]["is_correct"] is True
    assert by_kind["true_false"]["awarded"] == "1.00"
    assert by_kind["short_answer"]["awarded"] == "1.00"
    assert by_kind["multi_select"]["awarded"] == "2.00"  # partial credit
    assert by_kind["multi_select"]["is_correct"] is False

    essay = by_kind["essay"]
    assert essay["requires_manual_marking"] is True
    assert essay["awarded"] is None
    assert essay["auto_graded"] is False

    assert result.data["score"] == "6.00"
    assert result.data["max_score"] == "13.00"
    assert result.data["is_graded"] is False
    assert result.data["awaiting_manual_marking"] is True

    # The teacher marks the extended response; the attempt then closes out.
    marked = teacher.post(
        f"{BASE}/attempts/{attempt_id}/mark-answer/",
        {"answer": essay["answer"], "awarded_points": "4"},
        format="json",
    )
    assert marked.status_code == 200, marked.data
    assert marked.data["score"] == "10.00"
    assert marked.data["is_graded"] is True
    assert marked.data["awaiting_manual_marking"] is False


@pytest.mark.django_db
def test_multi_select_partial_credit_never_goes_negative(learner, quiz_bundle):
    started = _start(learner, quiz_bundle["quiz"])
    result = learner.post(
        f"{BASE}/attempts/{started.data['attempt']['id']}/submit/",
        {
            "answers": [
                {
                    "question": str(quiz_bundle["ms"].id),
                    # Both answers wrong: raw score would be -2/2, clamped to 0.
                    "choices": [str(quiz_bundle["ms_c"].id), str(quiz_bundle["ms_d"].id)],
                }
            ]
        },
        format="json",
    )
    ms_row = [r for r in result.data["questions"] if r["kind"] == "multi_select"][0]
    assert ms_row["awarded"] == "0.00"
    assert Decimal(result.data["score"]) >= Decimal("0")


@pytest.mark.django_db
def test_multi_select_full_marks_when_exactly_right(learner, quiz_bundle):
    started = _start(learner, quiz_bundle["quiz"])
    result = learner.post(
        f"{BASE}/attempts/{started.data['attempt']['id']}/submit/",
        {
            "answers": [
                {
                    "question": str(quiz_bundle["ms"].id),
                    "choices": [str(quiz_bundle["ms_a"].id), str(quiz_bundle["ms_b"].id)],
                }
            ]
        },
        format="json",
    )
    ms_row = [r for r in result.data["questions"] if r["kind"] == "multi_select"][0]
    assert ms_row["awarded"] == "4.00"
    assert ms_row["is_correct"] is True


@pytest.mark.django_db
def test_wrong_and_unanswered_questions_score_zero(learner, quiz_bundle):
    started = _start(learner, quiz_bundle["quiz"])
    result = learner.post(
        f"{BASE}/attempts/{started.data['attempt']['id']}/submit/",
        {
            "answers": [
                {"question": str(quiz_bundle["mc"].id), "choices": [str(quiz_bundle["mc_wrong"].id)]},
                {"question": str(quiz_bundle["sa"].id), "text_answer": "Fermat"},
            ]
        },
        format="json",
    )
    by_kind = {row["kind"]: row for row in result.data["questions"]}
    assert by_kind["multiple_choice"]["awarded"] == "0.00"
    assert by_kind["multiple_choice"]["is_correct"] is False
    assert by_kind["short_answer"]["awarded"] == "0.00"
    assert by_kind["true_false"]["answered"] is False
    assert by_kind["true_false"]["awarded"] == "0.00"
    assert result.data["score"] == "0.00"


@pytest.mark.django_db
def test_an_attempt_cannot_be_submitted_twice(learner, quiz_bundle):
    started = _start(learner, quiz_bundle["quiz"])
    attempt_id = started.data["attempt"]["id"]
    assert learner.post(f"{BASE}/attempts/{attempt_id}/submit/", {}, format="json").status_code == 200
    again = learner.post(f"{BASE}/attempts/{attempt_id}/submit/", {}, format="json")
    assert again.status_code == 400
    assert "already" in again.data["detail"].lower()


@pytest.mark.django_db
def test_answering_a_question_from_another_quiz_is_rejected(learner, tenant_id, section, quiz_bundle):
    other_quiz = Quiz.objects.create(
        tenant_id=tenant_id, class_section=section, title="Other", is_published=True
    )
    stray = Question.objects.create(
        tenant_id=tenant_id, quiz=other_quiz, text="Unrelated", kind="essay"
    )
    started = _start(learner, quiz_bundle["quiz"])
    bad = learner.post(
        f"{BASE}/attempts/{started.data['attempt']['id']}/answer/",
        {"question": str(stray.id), "text_answer": "x"},
        format="json",
    )
    assert bad.status_code == 400
    assert Answer.objects.count() == 0


@pytest.mark.django_db
def test_saving_an_answer_reveals_nothing_until_submission(learner, quiz_bundle):
    started = _start(learner, quiz_bundle["quiz"])
    attempt_id = started.data["attempt"]["id"]
    saved = learner.post(
        f"{BASE}/attempts/{attempt_id}/answer/",
        {"question": str(quiz_bundle["mc"].id), "choices": [str(quiz_bundle["mc_right"].id)]},
        format="json",
    )
    assert saved.status_code == 201, saved.data
    assert saved.data["is_correct"] is None
    assert saved.data["awarded_points"] is None

    # Review is refused before the attempt is handed in.
    early = learner.get(f"{BASE}/attempts/{attempt_id}/review/")
    assert early.status_code == 400

    learner.post(f"{BASE}/attempts/{attempt_id}/submit/", {}, format="json")
    review = learner.get(f"{BASE}/attempts/{attempt_id}/review/")
    assert review.status_code == 200
    mc_row = [r for r in review.data["questions"] if r["kind"] == "multiple_choice"][0]
    assert mc_row["is_correct"] is True
    # Only now is the key disclosed.
    assert mc_row["correct_choices"] == [str(quiz_bundle["mc_right"].id)]


@pytest.mark.django_db
def test_student_cannot_touch_another_students_attempt(
    learner, other_learner, quiz_bundle, student, other_student
):
    started = _start(other_learner, quiz_bundle["quiz"])
    attempt_id = started.data["attempt"]["id"]

    assert learner.get(f"{BASE}/attempts/{attempt_id}/").status_code == 404
    assert learner.get(f"{BASE}/attempts/{attempt_id}/review/").status_code == 404
    assert learner.post(f"{BASE}/attempts/{attempt_id}/submit/", {}, format="json").status_code == 404
    assert len(rows_of(learner.get(f"{BASE}/attempts/"))) == 0


@pytest.mark.django_db
def test_student_cannot_read_another_students_answers(
    learner, other_learner, quiz_bundle, student, other_student
):
    theirs = _start(other_learner, quiz_bundle["quiz"])
    other_learner.post(
        f"{BASE}/attempts/{theirs.data['attempt']['id']}/answer/",
        {"question": str(quiz_bundle["essay"].id), "text_answer": "their private essay"},
        format="json",
    )
    mine = _start(learner, quiz_bundle["quiz"])
    learner.post(
        f"{BASE}/attempts/{mine.data['attempt']['id']}/answer/",
        {"question": str(quiz_bundle["essay"].id), "text_answer": "my essay"},
        format="json",
    )

    listed = learner.get(f"{BASE}/answers/")
    assert listed.status_code == 200
    texts = [r["text_answer"] for r in rows_of(listed)]
    assert texts == ["my essay"]
    assert "their private essay" not in listed.content.decode()


@pytest.mark.django_db
def test_students_cannot_create_attempts_directly_or_mark_answers(
    learner, quiz_bundle, student
):
    direct = learner.post(
        f"{BASE}/attempts/",
        {"quiz": str(quiz_bundle["quiz"].id), "student": str(student.id)},
        format="json",
    )
    assert direct.status_code == 403

    started = _start(learner, quiz_bundle["quiz"])
    attempt_id = started.data["attempt"]["id"]
    learner.post(
        f"{BASE}/attempts/{attempt_id}/answer/",
        {"question": str(quiz_bundle["essay"].id), "text_answer": "essay"},
        format="json",
    )
    learner.post(f"{BASE}/attempts/{attempt_id}/submit/", {}, format="json")
    answer = Answer.objects.get(question=quiz_bundle["essay"])
    self_mark = learner.post(
        f"{BASE}/attempts/{attempt_id}/mark-answer/",
        {"answer": str(answer.id), "awarded_points": "5"},
        format="json",
    )
    assert self_mark.status_code == 403
    answer.refresh_from_db()
    assert answer.awarded_points is None


@pytest.mark.django_db
def test_account_without_a_student_record_cannot_sit_a_quiz(client_for, quiz_bundle):
    ghost = client_for(["student"], email="ghost@student.cyed.edu.au")
    # Not enrolled anywhere, so the quiz is not even visible.
    assert ghost.post(f"{BASE}/quizzes/{quiz_bundle['quiz'].id}/start/").status_code == 404


@pytest.mark.django_db
def test_teacher_starts_an_attempt_on_a_students_behalf(teacher, quiz_bundle, student):
    missing = teacher.post(f"{BASE}/quizzes/{quiz_bundle['quiz'].id}/start/", {}, format="json")
    assert missing.status_code == 400

    unknown = teacher.post(
        f"{BASE}/quizzes/{quiz_bundle['quiz'].id}/start/",
        {"student": str(uuid.uuid4())},
        format="json",
    )
    assert unknown.status_code == 400

    started = teacher.post(
        f"{BASE}/quizzes/{quiz_bundle['quiz'].id}/start/", {"student": str(student.id)}, format="json"
    )
    assert started.status_code == 201, started.data
    assert str(started.data["attempt"]["student"]) == str(student.id)


@pytest.mark.django_db
def test_expired_attempt_is_marked_on_what_was_already_saved(
    learner, tenant_id, section, student, quiz_bundle
):
    """A timed-out attempt is still marked rather than lost — Moodle-style."""
    quiz = quiz_bundle["quiz"]
    quiz.time_limit_minutes = 10
    quiz.save(update_fields=["time_limit_minutes"])

    attempt = QuizAttempt.objects.create(
        tenant_id=tenant_id, quiz=quiz, student=student, attempt_number=1,
        started_at=timezone.now() - timedelta(minutes=30), max_score=quiz.total_points,
    )
    assert attempt.is_expired is True
    services.save_answer(
        attempt, quiz_bundle["mc"], selected_choice_ids=[str(quiz_bundle["mc_right"].id)]
    )

    result = learner.post(
        f"{BASE}/attempts/{attempt.id}/submit/",
        {  # posted after the bell — ignored
            "answers": [
                {"question": str(quiz_bundle["tf"].id), "choices": [str(quiz_bundle["tf_true"].id)]}
            ]
        },
        format="json",
    )
    assert result.status_code == 200, result.data
    assert result.data["expired"] is True
    by_kind = {row["kind"]: row for row in result.data["questions"]}
    assert by_kind["multiple_choice"]["awarded"] == "2.00"  # saved in time
    assert by_kind["true_false"]["answered"] is False  # posted too late


@pytest.mark.django_db
def test_attempt_tenant_isolation(learner, tenant_id, quiz_bundle):
    foreign_tenant = uuid.uuid4()
    foreign_section = ClassSection.objects.create(
        tenant_id=foreign_tenant, name="Foreign", year_level=8
    )
    foreign_quiz = Quiz.objects.create(
        tenant_id=foreign_tenant, class_section=foreign_section, title="Foreign Quiz",
        is_published=True,
    )
    foreign_student = Student.objects.create(
        tenant_id=foreign_tenant, first_name="Ivy", last_name="Chen",
        year_level=8, email=STUDENT_EMAIL,  # same email, different tenant
    )
    QuizAttempt.objects.create(
        tenant_id=foreign_tenant, quiz=foreign_quiz, student=foreign_student, attempt_number=1
    )
    assert len(rows_of(learner.get(f"{BASE}/attempts/"))) == 0
    assert len(rows_of(learner.get(f"{BASE}/quizzes/"))) == 1


# ══════════════════════════ service-level units ══════════════════════════
@pytest.mark.django_db
def test_short_answer_matching_is_trimmed_and_case_insensitive(tenant_id, quiz_bundle, student):
    attempt = QuizAttempt.objects.create(
        tenant_id=tenant_id, quiz=quiz_bundle["quiz"], student=student, attempt_number=1
    )
    for raw, expected in [
        ("pythagoras", True),
        ("  PYTHAGOREAN   THEOREM ", True),
        ("Pythagoras!", False),
        ("", False),
    ]:
        answer = services.save_answer(attempt, quiz_bundle["sa"], text_answer=raw)
        services.grade_answer(answer)
        answer.refresh_from_db()
        assert answer.is_correct is expected, raw


@pytest.mark.django_db
def test_achievement_level_bands():
    assert services.achievement_level_for(90) == "A"
    assert services.achievement_level_for(70) == "B"
    assert services.achievement_level_for(50) == "C"
    assert services.achievement_level_for(30) == "D"
    assert services.achievement_level_for(10) == "E"
    assert services.achievement_level_for(None) == ""


@pytest.mark.django_db
def test_submit_submission_service_refuses_hard_deadline(tenant_id, section, student):
    closed = Assignment.objects.create(
        tenant_id=tenant_id, class_section=section, title="Closed",
        due_at=timezone.now() - timedelta(minutes=1), allow_late=False,
    )
    sub = Submission.objects.create(tenant_id=tenant_id, assignment=closed, student=student)
    with pytest.raises(services.LateSubmissionRefused):
        services.submit_submission(sub)
    sub.refresh_from_db()
    assert sub.status == "draft"
    assert sub.submitted_at is None


@pytest.mark.django_db
def test_manual_mark_is_clamped_to_the_question_maximum(tenant_id, quiz_bundle, student):
    attempt = QuizAttempt.objects.create(
        tenant_id=tenant_id, quiz=quiz_bundle["quiz"], student=student, attempt_number=1
    )
    answer = services.save_answer(attempt, quiz_bundle["essay"], text_answer="essay")
    services.mark_answer(answer, Decimal("99"))
    assert answer.awarded_points == Decimal("5.00")
    services.mark_answer(answer, Decimal("-4"))
    assert answer.awarded_points == Decimal("0.00")
