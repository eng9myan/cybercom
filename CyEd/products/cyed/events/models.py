from django.db import models

from platform.common.models import BaseModel


class Event(BaseModel):
    TYPES = [("assembly", "Assembly"), ("excursion", "Excursion"), ("sports", "Sports"),
             ("parent_evening", "Parent Evening"), ("other", "Other")]

    name = models.CharField(max_length=255)
    event_type = models.CharField(max_length=20, choices=TYPES, default="other")
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    requires_consent = models.BooleanField(default=False)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # ── excursion operations ────────────────────────────────────────────────
    # Consent and payment used to be two unrelated jobs: a form in docsign, a
    # charge in billing, and nobody able to answer the only question that
    # matters on the morning — who is allowed on the bus.
    permission_deadline = models.DateField(
        null=True, blank=True,
        help_text="After this, unreturned permissions are chased rather than waited on.",
    )
    staff_in_charge = models.ForeignKey(
        "cyed_hr.Staff", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="events_in_charge",
    )
    max_participants = models.PositiveSmallIntegerField(null=True, blank=True)
    departs_at = models.DateTimeField(null=True, blank=True)
    returns_at = models.DateTimeField(null=True, blank=True)
    transport_details = models.CharField(max_length=255, blank=True)
    what_to_bring = models.TextField(blank=True)
    # Some excursions are free, some are covered by the levy. Charging is
    # opt-in so a zero-cost event does not raise a nil invoice for every child.
    charge_students = models.BooleanField(default=False)
    # A child whose family cannot pay still goes. Recorded so the office can
    # see the difference between "not paid" and "not charged".
    hardship_waivers = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "cyed_events"
        ordering = ["start_at"]

    def is_excursion(self) -> bool:
        return self.event_type == "excursion" or self.requires_consent or self.charge_students

    def __str__(self):
        return self.name


class EventParticipation(BaseModel):
    STATUS = [("invited", "Invited"), ("confirmed", "Confirmed"), ("declined", "Declined")]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="participations")
    student = models.ForeignKey("cyed_sis.Student", on_delete=models.CASCADE, related_name="event_participations")
    status = models.CharField(max_length=20, choices=STATUS, default="invited")
    consent_given = models.BooleanField(default=False)
    responded_by = models.CharField(max_length=255, blank=True)

    # ── what makes a student cleared to go ──────────────────────────────────
    # Consent is evidenced by a signed document, not a boolean. The boolean
    # stays because other code reads it, but it is now a cached answer to
    # "is there a signed permission on file".
    consent_document = models.ForeignKey(
        "cyed_docsign.SignableDocument", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="event_participations",
    )
    consent_given_at = models.DateTimeField(null=True, blank=True)
    # The charge raised for this child, so "paid?" is answered from the ledger
    # rather than a second flag that drifts away from it.
    invoice = models.ForeignKey(
        "cyed_fees.Invoice", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="event_participations",
    )
    fee_waived = models.BooleanField(default=False)
    waiver_reason = models.CharField(max_length=255, blank=True)
    # Medical and dietary information the supervising teacher carries. Cached
    # at confirmation so a network drop on the day does not lose it.
    medical_notes_ack = models.BooleanField(default=False)
    emergency_contact = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_event_participations"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["event", "student"], name="uniq_participation_per_event_student")
        ]

    def is_paid(self) -> bool:
        """
        Paid, waived, or never charged. All three mean the money is not what
        is stopping this child getting on the bus.
        """
        if self.fee_waived or self.invoice_id is None:
            return True
        return self.invoice.balance <= 0

    def is_consented(self) -> bool:
        if not self.event.requires_consent:
            return True
        if self.consent_document_id:
            return self.consent_document.status == "completed"
        return self.consent_given

    def is_cleared(self) -> bool:
        """The only question that matters on the morning."""
        return (
            self.status == "confirmed"
            and self.is_consented()
            and self.is_paid()
        )

    def __str__(self):
        return f"{self.event_id} · {self.student_id} ({self.status})"
