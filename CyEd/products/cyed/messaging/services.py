"""
Thread access and posting rules.

The access question is deliberately separated from the role question. Roles say
what you may *do*; membership says what you may *see*. Conflating them is how a
"parent" role ends up reading every parent's correspondence.
"""

from django.db import transaction
from django.utils import timezone

from products.cyed.governance.access import (
    ADMIN,
    LEADERSHIP,
    PASTORAL,
    _email,
    has_any,
    is_staff,
    visible_student_ids,
)
from products.cyed.messaging.models import Message, MessageThread, ThreadParticipant


class MessagingError(Exception):
    """A messaging action was refused for a business reason (→ HTTP 400/409)."""


SAFEGUARDING_ROLES = PASTORAL | LEADERSHIP | ADMIN


def visible_threads(request, qs):
    """
    Threads this caller may read.

    Pastoral staff and leadership additionally see every thread involving a
    student, whether or not they are participants — adult↔child conversation
    must be observable, and a safeguarding oversight that depends on somebody
    remembering to add a supervisor is not oversight.
    """
    email = (_email(request) or "").lower()
    if has_any(request, ADMIN | LEADERSHIP):
        return qs

    mine = qs.filter(participants__email__iexact=email)
    if has_any(request, PASTORAL):
        safeguarded = qs.filter(kind__in=MessageThread.SAFEGUARDED_KINDS)
        return (mine | safeguarded).distinct()
    return mine.distinct()


def participant_for(thread, request):
    email = (_email(request) or "").lower()
    return thread.participants.filter(email__iexact=email).first()


def may_post(thread, request) -> tuple:
    """
    (allowed, reason). Posting requires membership — a supervising pastoral
    reader may watch a thread without joining the conversation, and should not
    be able to speak in it by accident.
    """
    if thread.is_closed:
        return False, "This conversation is closed. Start a new one to continue."
    if participant_for(thread, request) is None:
        return False, "You are not a participant in this conversation."
    return True, ""


def _resolve_student(request, student_id):
    from products.cyed.sis.models import Student

    if not student_id:
        return None
    student = Student.objects.filter(tenant_id=request.tenant_id, id=student_id).first()
    if student is None:
        raise MessagingError("No such student in this school.")
    # A guardian opening a thread may only name a child they can already see.
    visible = visible_student_ids(request, request.tenant_id)
    if visible is not None and student.id not in visible:
        raise MessagingError("You can only start a conversation about your own child.")
    return student


def _participant_rows(request, thread, *, staff_ids, guardian_ids, student_ids):
    """Build participant rows, resolving each party to a real record."""
    from products.cyed.hr.models import Staff
    from products.cyed.sis.models import Guardian, Student

    tenant = request.tenant_id
    rows = []

    for staff in Staff.objects.filter(tenant_id=tenant, id__in=staff_ids or []):
        rows.append(ThreadParticipant(
            tenant_id=tenant, thread=thread, party_kind="staff",
            email=(staff.email or "").lower(),
            display_name=f"{staff.first_name} {staff.last_name}".strip(),
            staff=staff,
        ))
    for guardian in Guardian.objects.filter(tenant_id=tenant, id__in=guardian_ids or []):
        rows.append(ThreadParticipant(
            tenant_id=tenant, thread=thread, party_kind="guardian",
            email=(guardian.email or "").lower(),
            display_name=f"{guardian.first_name} {guardian.last_name}".strip(),
            guardian=guardian,
        ))
    for student in Student.objects.filter(tenant_id=tenant, id__in=student_ids or []):
        rows.append(ThreadParticipant(
            tenant_id=tenant, thread=thread, party_kind="student",
            email=(student.email or "").lower(),
            display_name=f"{student.first_name} {student.last_name}".strip(),
            student=student,
        ))

    missing = [r for r in rows if not r.email]
    if missing:
        # Access is decided by email; a participant without one could never
        # read the thread, so adding them would quietly do nothing.
        names = ", ".join(r.display_name or "(unnamed)" for r in missing)
        raise MessagingError(
            f"These participants have no email address on record and could not be "
            f"added: {names}."
        )
    return rows


@transaction.atomic
def open_thread(
    request, *, subject, body, kind="teacher_parent", student_id=None,
    staff_ids=None, guardian_ids=None, student_ids=None,
):
    """
    Start a conversation and post its first message.

    The opener is always a participant — a thread you started but cannot read
    would be an odd kind of nothing.
    """
    if not (subject or "").strip():
        raise MessagingError("Give the conversation a subject.")
    if not (body or "").strip():
        raise MessagingError("A conversation starts with a message.")

    student = _resolve_student(request, student_id)
    email = (_email(request) or "").lower()
    if not email:
        raise MessagingError("This account has no email address, so it cannot send messages.")

    thread = MessageThread.objects.create(
        tenant_id=request.tenant_id, subject=subject.strip()[:255], kind=kind,
        student=student, opened_by_email=email,
    )

    rows = _participant_rows(
        request, thread,
        staff_ids=staff_ids, guardian_ids=guardian_ids, student_ids=student_ids,
    )
    ThreadParticipant.objects.bulk_create(rows)

    if not thread.participants.filter(email__iexact=email).exists():
        ThreadParticipant.objects.create(
            tenant_id=request.tenant_id, thread=thread,
            party_kind="staff" if is_staff(request) else "guardian",
            email=email, display_name=email,
        )

    if thread.participants.count() < 2:
        raise MessagingError(
            "A conversation needs someone to talk to — add at least one other participant."
        )

    post_message(request, thread, body)
    return thread


def post_message(request, thread, body):
    """Append a message and stamp the thread's activity time."""
    if not (body or "").strip():
        raise MessagingError("An empty message says nothing; write something or don't send.")

    allowed, reason = may_post(thread, request)
    if not allowed:
        raise MessagingError(reason)

    participant = participant_for(thread, request)
    now = timezone.now()
    message = Message.objects.create(
        tenant_id=thread.tenant_id, thread=thread,
        sender_kind=participant.party_kind,
        sender_email=participant.email,
        sender_name=participant.display_name,
        body=body.strip(),
        sent_at=now,
    )
    thread.last_message_at = now
    thread.save(update_fields=["last_message_at", "updated_at"])

    # Sending is also reading, otherwise your own message shows as unread.
    participant.last_read_at = now
    participant.save(update_fields=["last_read_at", "updated_at"])
    return message


def mark_read(thread, request):
    participant = participant_for(thread, request)
    if participant is None:
        return None
    participant.last_read_at = timezone.now()
    participant.save(update_fields=["last_read_at", "updated_at"])
    return participant


def inbox(request, qs):
    """Threads with unread counts, most recently active first."""
    rows = []
    for thread in visible_threads(request, qs).prefetch_related("participants", "messages"):
        participant = participant_for(thread, request)
        last = thread.messages.last()
        rows.append({
            "thread": str(thread.id),
            "subject": thread.subject,
            "kind": thread.kind,
            "student": str(thread.student_id) if thread.student_id else None,
            "is_closed": thread.is_closed,
            "participants": [p.display_name or p.email for p in thread.participants.all()],
            "last_message_at": thread.last_message_at,
            "last_message_preview": (last.body[:120] if last else ""),
            "last_sender": (last.sender_name or last.sender_email) if last else "",
            "unread": participant.unread_count() if participant else 0,
            # True when the caller is reading this only in a supervisory
            # capacity, so a UI can say so rather than implying they are part
            # of the conversation.
            "observing": participant is None,
        })
    rows.sort(key=lambda r: (r["last_message_at"] is None, r["last_message_at"]), reverse=True)
    return rows
