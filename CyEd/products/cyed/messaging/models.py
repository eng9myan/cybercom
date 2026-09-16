"""
Two-way messaging between school and home.

`notifications` is send-only: staff push a message out and nothing comes back.
There was no teacher↔parent thread, no reply path, and no student↔teacher
channel at all — so the most ordinary interaction in a school, a parent
answering a message about their child, happened by email outside the system and
left no record attached to the student.

Three decisions are load-bearing here:

**Participation is the access rule.** Nobody reads a thread they are not in.
Roles decide what you may *do* (staff open threads, parents reply); membership
decides what you may *see*. Anything else ends with a parent reading another
family's correspondence.

**Adult↔child conversations are never private.** A thread with a student
participant is always readable by pastoral staff and leadership, whether or not
they are participants. Unobservable one-to-one messaging between an adult and a
child is a safeguarding hazard, and a school system that offered it would be
building the hazard in. This is deliberate and is not configurable.

**Messages are immutable.** Correspondence with families is a record that gets
produced in disputes. A message that can be edited after the fact is not
evidence of what was said.
"""

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class MessageThread(BaseModel):
    KIND_CHOICES = [
        ("teacher_parent", "Teacher ↔ parent"),
        ("teacher_student", "Teacher ↔ student"),
        ("office_parent", "Office ↔ parent"),
        ("staff_staff", "Staff ↔ staff"),
    ]
    # Kinds that put a child in the conversation. These are always visible to
    # pastoral staff and leadership — see the module docstring.
    SAFEGUARDED_KINDS = {"teacher_student"}

    subject = models.CharField(max_length=255)
    kind = models.CharField(max_length=30, choices=KIND_CHOICES, default="teacher_parent")
    # The child the conversation is about. Most school↔home correspondence is,
    # and attaching it is what makes the thread findable from the student
    # record rather than only from someone's inbox.
    student = models.ForeignKey(
        "cyed_sis.Student", on_delete=models.CASCADE, null=True, blank=True,
        related_name="message_threads",
    )
    opened_by_email = models.CharField(max_length=255, blank=True)
    is_closed = models.BooleanField(default=False)
    closed_on = models.DateTimeField(null=True, blank=True)
    closed_by_email = models.CharField(max_length=255, blank=True)
    # Denormalised so an inbox can sort without touching every message.
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cyed_message_threads"
        ordering = ["-last_message_at", "-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "-last_message_at"], name="idx_thread_recent"),
        ]

    def close(self, by_email=""):
        self.is_closed = True
        self.closed_on = timezone.now()
        self.closed_by_email = by_email[:255]
        self.save(update_fields=["is_closed", "closed_on", "closed_by_email", "updated_at"])

    def involves_a_student(self) -> bool:
        return self.kind in self.SAFEGUARDED_KINDS or self.participants.filter(
            party_kind="student"
        ).exists()

    def __str__(self):
        return f"{self.subject} ({self.kind})"


class ThreadParticipant(BaseModel):
    """
    Who is in a conversation.

    Identity is matched on `email` because that is what arrives in the token —
    the FKs are there so the thread can be reported against a real person, but
    access is decided by the email, which is the only thing an authenticated
    request actually proves.
    """

    PARTY_CHOICES = [
        ("staff", "Staff"),
        ("guardian", "Guardian"),
        ("student", "Student"),
    ]

    thread = models.ForeignKey(
        MessageThread, on_delete=models.CASCADE, related_name="participants"
    )
    party_kind = models.CharField(max_length=20, choices=PARTY_CHOICES)
    email = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True)

    staff = models.ForeignKey(
        "cyed_hr.Staff", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="message_threads",
    )
    guardian = models.ForeignKey(
        "cyed_sis.Guardian", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="message_threads",
    )
    student = models.ForeignKey(
        "cyed_sis.Student", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="thread_memberships",
    )
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cyed_thread_participants"
        ordering = ["party_kind", "display_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["thread", "email"], name="uniq_participant_email_per_thread"
            ),
        ]

    def unread_count(self) -> int:
        qs = self.thread.messages.all()
        if self.last_read_at:
            qs = qs.filter(sent_at__gt=self.last_read_at)
        # Your own messages are never unread to you.
        return qs.exclude(sender_email__iexact=self.email).count()

    def __str__(self):
        return f"{self.display_name or self.email} in {self.thread_id}"


class Message(BaseModel):
    """One message. Append-only: no edit, no delete."""

    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name="messages")
    sender_kind = models.CharField(max_length=20, choices=ThreadParticipant.PARTY_CHOICES)
    sender_email = models.CharField(max_length=255)
    sender_name = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cyed_messages"
        ordering = ["sent_at"]
        indexes = [
            models.Index(fields=["tenant_id", "thread", "sent_at"], name="idx_message_thread_time"),
        ]

    def __str__(self):
        return f"{self.sender_email}: {self.body[:40]}"
