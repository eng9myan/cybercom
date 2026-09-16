from django.db import models

from platform.common.models import BaseModel


class Notification(BaseModel):
    """
    A message to a guardian/student/staff member. `in_app` notifications are
    delivered immediately (stored, visible in the portal); email/sms/push are
    delivered via an env-gated provider seam (default: queued until configured).
    """

    RECIPIENT_KINDS = [
        ("guardian", "Guardian"),
        ("student", "Student"),
        ("staff", "Staff"),
        ("other", "Other"),
    ]
    CHANNELS = [
        ("in_app", "In-App"),
        ("email", "Email"),
        ("sms", "SMS"),
        ("push", "Push"),
        ("whatsapp", "WhatsApp"),
    ]
    CATEGORIES = [
        ("attendance", "Attendance"),
        ("announcement", "Announcement"),
        ("billing", "Billing"),
        ("wellbeing", "Wellbeing"),
        ("general", "General"),
    ]
    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("sent", "Sent"),
        ("failed", "Failed"),
        ("read", "Read"),
    ]

    student = models.ForeignKey(
        "cyed_sis.Student", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="notifications",
    )
    recipient_kind = models.CharField(max_length=20, choices=RECIPIENT_KINDS, default="guardian")
    recipient_name = models.CharField(max_length=255, blank=True)
    recipient_email = models.CharField(max_length=255, blank=True)
    recipient_phone = models.CharField(max_length=50, blank=True)
    channel = models.CharField(max_length=20, choices=CHANNELS, default="in_app")
    category = models.CharField(max_length=20, choices=CATEGORIES, default="general")
    subject = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    related_model = models.CharField(max_length=100, blank=True)
    related_id = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    error = models.CharField(max_length=255, blank=True)
    # Which transport carried it, and the id that transport gave it. Kept so a
    # parent saying "I never got the text" can be answered from the provider's
    # own logs instead of a shrug.
    provider = models.CharField(max_length=40, blank=True)
    provider_reference = models.CharField(max_length=120, blank=True)

    class Meta:
        db_table = "cyed_notifications"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["tenant_id", "recipient_email"])]

    def __str__(self):
        return f"[{self.channel}/{self.status}] {self.subject} → {self.recipient_name}"


class PushDevice(BaseModel):
    """
    A device that has agreed to receive push notifications.

    `push` was a channel choice with nothing behind it: no registration, no
    tokens, and `delivery.py` refused the channel outright. A school could set
    it and believe alerts were going out.

    Tokens are keyed to an **email**, not a user id, because that is what the
    JWT actually proves and what every other recipient lookup in the product
    uses. A person with a phone and a laptop has two rows; both get the message.
    """

    PLATFORM_CHOICES = [
        ("web", "Web push"),
        ("ios", "iOS"),
        ("android", "Android"),
    ]

    owner_email = models.CharField(max_length=255)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default="web")
    # Web push needs the endpoint plus two keys; native platforms need only a
    # token. Kept in one model because the delivery seam is the same.
    token = models.TextField()
    endpoint = models.TextField(blank=True)
    p256dh = models.CharField(max_length=255, blank=True)
    auth = models.CharField(max_length=255, blank=True)
    label = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    # Set when the provider tells us the token is dead. Kept rather than
    # deleted so a device that reappears is recognised rather than re-registered.
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_push_devices"
        ordering = ["-last_used_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "token"], name="uniq_push_token_per_tenant"
            ),
        ]
        indexes = [
            models.Index(fields=["tenant_id", "owner_email"], name="idx_push_owner"),
        ]

    def __str__(self):
        return f"{self.platform} device for {self.owner_email}"


class Newsletter(BaseModel):
    """
    A bulk message to an audience — the weekly newsletter, a principal's note.

    Distinct from `Notification`, which is one message to one recipient. A
    newsletter is composed once, targeted, and then *fans out* into ordinary
    notifications so it travels the same delivery path as everything else and
    inherits the same honesty about what was actually sent.

    Drafts are the default and sending is explicit. A newsletter that goes out
    the moment it is saved is one a school sends by accident, to everybody.
    """

    AUDIENCE_CHOICES = [
        ("parents", "Parents and guardians"),
        ("staff", "Staff"),
        ("students", "Students"),
        ("all", "Everyone"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sending", "Sending"),
        ("sent", "Sent"),
    ]

    title = models.CharField(max_length=255)
    body = models.TextField()
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default="parents")
    # Blank means every year level; "9,10" narrows it.
    year_levels = models.CharField(max_length=100, blank=True)
    campus = models.ForeignKey(
        "cyed_org.Campus", on_delete=models.CASCADE, null=True, blank=True,
        related_name="newsletters",
    )
    channel = models.CharField(
        max_length=20, default="in_app",
        help_text="in_app, email or push. SMS is deliberately not offered for bulk.",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_by = models.CharField(max_length=255, blank=True)
    recipients = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cyed_newsletters"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.status})"
