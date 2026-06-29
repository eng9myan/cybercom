from django.db import models

from platform.common.models import BaseModel


class PortalAppointmentRequest(BaseModel):
    PROVIDER_TYPE_CHOICES = [
        ("hospital", "Hospital"),
        ("clinic", "Clinic"),
        ("telemedicine", "Telemedicine"),
    ]
    TIME_SLOT_CHOICES = [
        ("morning", "Morning"),
        ("afternoon", "Afternoon"),
        ("evening", "Evening"),
        ("any", "Any"),
    ]
    APPOINTMENT_TYPE_CHOICES = [
        ("consultation", "Consultation"),
        ("follow_up", "Follow Up"),
        ("procedure", "Procedure"),
        ("vaccination", "Vaccination"),
        ("checkup", "Checkup"),
        ("telemedicine", "Telemedicine"),
        ("home_visit", "Home Visit"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("rescheduled", "Rescheduled"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
        ("no_show", "No Show"),
    ]
    CANCELLED_BY_CHOICES = [
        ("patient", "Patient"),
        ("provider", "Provider"),
        ("system", "System"),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    is_for_dependent = models.BooleanField(default=False)
    dependent_patient_id = models.UUIDField(null=True, blank=True)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPE_CHOICES, default="clinic")
    provider_id = models.UUIDField(null=True, blank=True)
    provider_name = models.CharField(max_length=255, blank=True)
    specialty = models.CharField(max_length=100, blank=True)
    physician_id = models.UUIDField(null=True, blank=True)
    physician_name = models.CharField(max_length=255, blank=True)
    preferred_date_1 = models.DateField(null=True, blank=True)
    preferred_date_2 = models.DateField(null=True, blank=True)
    preferred_date_3 = models.DateField(null=True, blank=True)
    preferred_time_slot = models.CharField(max_length=20, choices=TIME_SLOT_CHOICES, default="any")
    appointment_type = models.CharField(
        max_length=20, choices=APPOINTMENT_TYPE_CHOICES, default="consultation"
    )
    chief_complaint = models.TextField(blank=True)
    insurance_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    confirmed_datetime = models.DateTimeField(null=True, blank=True)
    confirmed_location = models.CharField(max_length=500, blank=True)
    cymed_appointment_id = models.UUIDField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    cancelled_by = models.CharField(max_length=20, choices=CANCELLED_BY_CHOICES, blank=True)
    reminder_sent = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_portal_appointment_requests"
        indexes = [
            models.Index(fields=["account_id", "status"]),
            models.Index(fields=["patient_id", "status"]),
            models.Index(fields=["provider_id", "preferred_date_1"]),
        ]

    def __str__(self):
        return f"AppointmentRequest {self.id} - {self.patient_id} [{self.status}]"


class WaitlistEntry(BaseModel):
    WAITLIST_TYPE_CHOICES = [
        ("next_available", "Next Available"),
        ("specific_physician", "Specific Physician"),
        ("specific_date", "Specific Date"),
    ]
    PRIORITY_CHOICES = [
        ("routine", "Routine"),
        ("urgent", "Urgent"),
        ("stat", "Stat"),
    ]
    STATUS_CHOICES = [
        ("waiting", "Waiting"),
        ("offered", "Offered"),
        ("accepted", "Accepted"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    provider_id = models.UUIDField(db_index=True)
    specialty = models.CharField(max_length=100, blank=True)
    physician_id = models.UUIDField(null=True, blank=True)
    waitlist_type = models.CharField(
        max_length=30, choices=WAITLIST_TYPE_CHOICES, default="next_available"
    )
    earliest_date = models.DateField(null=True, blank=True)
    latest_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="routine")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="waiting")
    offered_slot = models.DateTimeField(null=True, blank=True)
    offer_expires_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_portal_waitlist"
        indexes = [
            models.Index(fields=["account_id", "status"]),
            models.Index(fields=["provider_id", "status"]),
        ]

    def __str__(self):
        return f"WaitlistEntry {self.id} - {self.patient_id} [{self.status}]"


class AppointmentReminder(BaseModel):
    REMINDER_TYPE_CHOICES = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("push", "Push"),
        ("in_app", "In App"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    appointment_request = models.ForeignKey(
        PortalAppointmentRequest,
        on_delete=models.CASCADE,
        related_name="reminders",
    )
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPE_CHOICES, default="push")
    scheduled_at = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    reminder_hours_before = models.PositiveSmallIntegerField(default=24)

    class Meta:
        db_table = "cymed_portal_appointment_reminders"

    def __str__(self):
        return f"Reminder {self.id} for {self.appointment_request_id} [{self.status}]"


class AppointmentRating(BaseModel):
    appointment_request = models.OneToOneField(
        PortalAppointmentRequest,
        on_delete=models.CASCADE,
        related_name="rating",
    )
    account_id = models.UUIDField(db_index=True)
    overall_rating = models.PositiveSmallIntegerField()
    wait_time_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    staff_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    facility_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    physician_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    comment = models.TextField(blank=True)
    would_recommend = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_portal_appointment_ratings"

    def __str__(self):
        return f"Rating {self.id} for appointment {self.appointment_request_id} - {self.overall_rating}/5"
