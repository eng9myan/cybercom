"""
Two-way messaging.

Most of these tests are about who can *read* what. Roles decide what you may
do; membership decides what you may see — and the one deliberate exception is
safeguarding: adult↔child threads are always observable by pastoral staff.
"""

import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.hr.models import Staff
from products.cyed.messaging.models import Message, MessageThread
from products.cyed.sis.models import Guardian, Student


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token({
            'sub': str(uuid.uuid4()), 'email': email, 'tenant_id': str(tenant_id),
            'realm_access': {'roles': roles},
        })}")
        return c
    return _make


@pytest.fixture
def cast(tenant_id):
    teacher = Staff.objects.create(
        tenant_id=tenant_id, first_name="Ada", last_name="Lovelace",
        role="teacher", email="ada@cyed.edu.au",
    )
    student = Student.objects.create(
        tenant_id=tenant_id, first_name="Mia", last_name="Tran", year_level=8,
        enrolment_status="enrolled", email="mia@student.cyed.edu.au",
    )
    parent = Guardian.objects.create(
        tenant_id=tenant_id, first_name="Hoa", last_name="Tran", email="hoa@example.com",
    )
    parent.students.add(student)

    other_student = Student.objects.create(
        tenant_id=tenant_id, first_name="Ken", last_name="Ito", year_level=8,
        enrolment_status="enrolled",
    )
    other_parent = Guardian.objects.create(
        tenant_id=tenant_id, first_name="Yui", last_name="Ito", email="yui@example.com",
    )
    other_parent.students.add(other_student)
    return teacher, student, parent, other_student, other_parent


@pytest.fixture
def teacher_client(client_for):
    return client_for(["teacher"], "ada@cyed.edu.au")


@pytest.fixture
def parent_client(client_for):
    return client_for(["parent"], "hoa@example.com")


@pytest.fixture
def other_parent_client(client_for):
    return client_for(["parent"], "yui@example.com")


def _open(client, cast, **overrides):
    teacher, student, parent, *_ = cast
    body = {
        "subject": "Mia's progress in Maths",
        "body": "Mia has made a strong start this term.",
        "kind": "teacher_parent",
        "student": str(student.id),
        "staff": [str(teacher.id)],
        "guardians": [str(parent.id)],
    }
    body.update(overrides)
    return client.post("/api/v1/messaging/threads/open/", body, format="json")


# ── the reply path that did not exist ────────────────────────────────────────
@pytest.mark.django_db
def test_a_teacher_opens_a_thread_and_a_parent_replies(teacher_client, parent_client, cast):
    opened = _open(teacher_client, cast)
    assert opened.status_code == 201, opened.data
    thread_id = opened.data["id"]

    reply = parent_client.post(f"/api/v1/messaging/threads/{thread_id}/reply/", {
        "body": "Thank you — she's enjoying it.",
    }, format="json")
    assert reply.status_code == 201, reply.data

    thread = MessageThread.objects.get(id=thread_id)
    assert thread.messages.count() == 2
    assert [m.sender_kind for m in thread.messages.all()] == ["staff", "guardian"]


@pytest.mark.django_db
def test_the_opener_is_always_a_participant(teacher_client, cast):
    """A thread you started but cannot read would be an odd kind of nothing."""
    opened = _open(teacher_client, cast, staff=[])
    assert opened.status_code == 201
    emails = {p["email"] for p in opened.data["participants"]}
    assert "ada@cyed.edu.au" in emails


@pytest.mark.django_db
def test_a_thread_needs_someone_to_talk_to(teacher_client, cast):
    resp = _open(teacher_client, cast, staff=[], guardians=[])
    assert resp.status_code == 400
    assert "someone to talk to" in resp.data["detail"]


@pytest.mark.django_db
def test_an_empty_message_is_refused(teacher_client, parent_client, cast):
    thread_id = _open(teacher_client, cast).data["id"]
    resp = parent_client.post(
        f"/api/v1/messaging/threads/{thread_id}/reply/", {"body": "   "}, format="json"
    )
    assert resp.status_code == 409


# ── access is membership, not role ───────────────────────────────────────────
@pytest.mark.django_db
def test_another_parent_cannot_read_the_thread(teacher_client, other_parent_client, cast):
    thread_id = _open(teacher_client, cast).data["id"]
    assert other_parent_client.get(
        f"/api/v1/messaging/threads/{thread_id}/"
    ).status_code == 404


@pytest.mark.django_db
def test_another_parent_cannot_reply_to_it(teacher_client, other_parent_client, cast):
    thread_id = _open(teacher_client, cast).data["id"]
    resp = other_parent_client.post(
        f"/api/v1/messaging/threads/{thread_id}/reply/", {"body": "hello"}, format="json"
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_an_uninvolved_teacher_cannot_read_the_thread(teacher_client, client_for, tenant_id, cast):
    """Holding the teacher role is not membership of every conversation."""
    Staff.objects.create(
        tenant_id=tenant_id, first_name="Bob", last_name="Other",
        role="teacher", email="bob@cyed.edu.au",
    )
    thread_id = _open(teacher_client, cast).data["id"]
    stranger = client_for(["teacher"], "bob@cyed.edu.au")
    assert stranger.get(f"/api/v1/messaging/threads/{thread_id}/").status_code == 404


@pytest.mark.django_db
def test_a_parent_cannot_open_a_thread_about_someone_elses_child(parent_client, cast):
    teacher, _student, parent, other_student, _other_parent = cast
    resp = parent_client.post("/api/v1/messaging/threads/open/", {
        "subject": "About Ken", "body": "A question.",
        "student": str(other_student.id),
        "staff": [str(teacher.id)], "guardians": [str(parent.id)],
    }, format="json")
    assert resp.status_code == 400
    assert "your own child" in resp.data["detail"]


@pytest.mark.django_db
def test_messages_are_scoped_to_readable_threads(teacher_client, other_parent_client, cast):
    _open(teacher_client, cast)
    resp = other_parent_client.get("/api/v1/messaging/messages/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert rows == []


# ── safeguarding ─────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_teacher_student_threads_are_observable_by_pastoral_staff(
    teacher_client, client_for, cast
):
    """
    Unobservable one-to-one messaging between an adult and a child is a
    safeguarding hazard. Oversight that depends on someone remembering to add
    a supervisor is not oversight.
    """
    teacher, student, *_ = cast
    opened = teacher_client.post("/api/v1/messaging/threads/open/", {
        "subject": "Your assignment", "body": "Please resubmit question 3.",
        "kind": "teacher_student", "student": str(student.id),
        "staff": [str(teacher.id)], "students": [str(student.id)],
    }, format="json")
    assert opened.status_code == 201, opened.data

    counsellor = client_for(["pastoral"], "counsellor@cyed.edu.au")
    resp = counsellor.get(f"/api/v1/messaging/threads/{opened.data['id']}/")
    assert resp.status_code == 200
    assert resp.data["subject"] == "Your assignment"


@pytest.mark.django_db
def test_a_pastoral_observer_cannot_speak_in_the_thread(teacher_client, client_for, cast):
    """Watching a conversation must not make it possible to join it by accident."""
    teacher, student, *_ = cast
    opened = teacher_client.post("/api/v1/messaging/threads/open/", {
        "subject": "Your assignment", "body": "Please resubmit question 3.",
        "kind": "teacher_student", "student": str(student.id),
        "staff": [str(teacher.id)], "students": [str(student.id)],
    }, format="json")
    counsellor = client_for(["pastoral"], "counsellor@cyed.edu.au")
    resp = counsellor.post(
        f"/api/v1/messaging/threads/{opened.data['id']}/reply/", {"body": "hi"}, format="json"
    )
    assert resp.status_code == 409
    assert "not a participant" in resp.data["detail"]


@pytest.mark.django_db
def test_pastoral_staff_do_not_get_to_read_parent_threads_they_are_not_in(
    teacher_client, client_for, cast
):
    """The safeguarding exception is for threads involving a child, not everything."""
    thread_id = _open(teacher_client, cast).data["id"]   # teacher_parent
    counsellor = client_for(["pastoral"], "counsellor@cyed.edu.au")
    assert counsellor.get(f"/api/v1/messaging/threads/{thread_id}/").status_code == 404


# ── inbox and unread ─────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_unread_counts_your_own_messages_as_read(teacher_client, parent_client, cast):
    thread_id = _open(teacher_client, cast).data["id"]

    teacher_inbox = teacher_client.get("/api/v1/messaging/threads/inbox/")
    assert teacher_inbox.data["results"][0]["unread"] == 0   # they sent it

    parent_inbox = parent_client.get("/api/v1/messaging/threads/inbox/")
    assert parent_inbox.data["results"][0]["unread"] == 1
    assert parent_inbox.data["results"][0]["observing"] is False


@pytest.mark.django_db
def test_marking_read_clears_the_count(teacher_client, parent_client, cast):
    thread_id = _open(teacher_client, cast).data["id"]
    parent_client.post(f"/api/v1/messaging/threads/{thread_id}/mark-read/", {}, format="json")
    inbox = parent_client.get("/api/v1/messaging/threads/inbox/")
    assert inbox.data["results"][0]["unread"] == 0


@pytest.mark.django_db
def test_replying_marks_your_own_side_read(teacher_client, parent_client, cast):
    thread_id = _open(teacher_client, cast).data["id"]
    parent_client.post(
        f"/api/v1/messaging/threads/{thread_id}/reply/", {"body": "Thanks"}, format="json"
    )
    inbox = parent_client.get("/api/v1/messaging/threads/inbox/")
    assert inbox.data["results"][0]["unread"] == 0


@pytest.mark.django_db
def test_an_observer_is_labelled_as_observing(teacher_client, client_for, cast):
    teacher, student, *_ = cast
    teacher_client.post("/api/v1/messaging/threads/open/", {
        "subject": "Assignment", "body": "Resubmit please.",
        "kind": "teacher_student", "student": str(student.id),
        "staff": [str(teacher.id)], "students": [str(student.id)],
    }, format="json")
    counsellor = client_for(["pastoral"], "counsellor@cyed.edu.au")
    inbox = counsellor.get("/api/v1/messaging/threads/inbox/")
    assert inbox.data["results"][0]["observing"] is True


# ── closing ──────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_staff_can_close_a_thread_and_replies_stop(teacher_client, parent_client, cast):
    thread_id = _open(teacher_client, cast).data["id"]
    assert teacher_client.post(
        f"/api/v1/messaging/threads/{thread_id}/close/", {}, format="json"
    ).status_code == 200

    resp = parent_client.post(
        f"/api/v1/messaging/threads/{thread_id}/reply/", {"body": "One more thing"}, format="json"
    )
    assert resp.status_code == 409
    assert "closed" in resp.data["detail"]


@pytest.mark.django_db
def test_a_parent_cannot_close_a_thread(teacher_client, parent_client, cast):
    """A family cannot end a conversation the school still needs an answer in."""
    thread_id = _open(teacher_client, cast).data["id"]
    resp = parent_client.post(
        f"/api/v1/messaging/threads/{thread_id}/close/", {}, format="json"
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_closing_preserves_the_record(teacher_client, cast):
    thread_id = _open(teacher_client, cast).data["id"]
    teacher_client.post(f"/api/v1/messaging/threads/{thread_id}/close/", {}, format="json")
    resp = teacher_client.get(f"/api/v1/messaging/threads/{thread_id}/")
    assert resp.status_code == 200
    assert len(resp.data["messages"]) == 1


# ── immutability ─────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_message_cannot_be_edited_or_deleted(teacher_client, cast):
    """Correspondence with families is a record, not a draft."""
    thread_id = _open(teacher_client, cast).data["id"]
    message = Message.objects.filter(thread_id=thread_id).first()
    assert teacher_client.patch(
        f"/api/v1/messaging/messages/{message.id}/", {"body": "different"}, format="json"
    ).status_code == 405
    assert teacher_client.delete(f"/api/v1/messaging/messages/{message.id}/").status_code == 405


@pytest.mark.django_db
def test_a_thread_cannot_be_created_by_posting_a_bare_row(teacher_client, cast):
    """That path would bypass participation and safeguarding entirely."""
    resp = teacher_client.post("/api/v1/messaging/threads/", {
        "subject": "Sneaky", "kind": "teacher_parent",
    }, format="json")
    assert resp.status_code in (400, 405)
    assert not MessageThread.objects.filter(subject="Sneaky").exists()


@pytest.mark.django_db
def test_a_participant_without_an_email_is_refused_rather_than_silently_ignored(
    teacher_client, tenant_id, cast
):
    """Access is decided by email; adding someone without one would do nothing."""
    teacher, student, parent, *_ = cast
    emailless = Guardian.objects.create(
        tenant_id=tenant_id, first_name="No", last_name="Email"
    )
    emailless.students.add(student)
    resp = _open(teacher_client, cast, guardians=[str(parent.id), str(emailless.id)])
    assert resp.status_code == 400
    assert "no email address on record" in resp.data["detail"]
