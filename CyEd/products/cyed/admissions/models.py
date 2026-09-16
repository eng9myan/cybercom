from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class CatchmentZone(BaseModel):
    """
    The area a campus draws from.

    Government schools enrol from a designated zone and many independent
    schools price or prioritise by one. Without a zone model there is nothing
    to check an address against at enrolment, so a registrar has to know the
    boundary by heart — which is how out-of-zone enrolments get accepted and
    then have to be unwound.

    Matching is on suburb and postcode rather than geometry: that is the
    granularity Australian school zones are actually published at, and it needs
    no spatial database.
    """

    name = models.CharField(max_length=150)
    campus = models.ForeignKey(
        "cyed_org.Campus", on_delete=models.CASCADE, null=True, blank=True,
        related_name="catchment_zones",
    )
    postcodes = models.JSONField(default=list, blank=True, help_text='e.g. ["3121", "3122"]')
    suburbs = models.JSONField(default=list, blank=True, help_text='e.g. ["Richmond", "Hawthorn"]')
    # A priority zone gets first call on places before general applicants.
    is_priority = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_catchment_zones"
        ordering = ["-is_priority", "name"]

    def covers(self, *, suburb="", postcode="") -> bool:
        if postcode and str(postcode).strip() in {str(p).strip() for p in self.postcodes}:
            return True
        if suburb and suburb.strip().casefold() in {
            str(s).strip().casefold() for s in self.suburbs
        }:
            return True
        return False

    def __str__(self):
        return f"{self.name}{' (priority)' if self.is_priority else ''}"


class Application(BaseModel):
    STATUS_CHOICES = [
        ("enquiry", "Enquiry"),
        ("submitted", "Submitted"),
        ("assessment", "Under Assessment"),
        ("offer", "Offer Made"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
        ("waitlisted", "Waitlisted"),
        ("withdrawn", "Withdrawn"),
        ("enrolled", "Enrolled"),
    ]

    applicant_first_name = models.CharField(max_length=100)
    applicant_last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    year_level_applying = models.PositiveSmallIntegerField(default=7)
    guardian_name = models.CharField(max_length=255, blank=True)
    guardian_email = models.EmailField(blank=True)
    guardian_phone = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="enquiry")
    source = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    # Set when the application is converted into an enrolled student.
    enrolled_student_id = models.UUIDField(null=True, blank=True)

    # Address, so catchment can be checked at all. Stored on the application
    # rather than only on the eventual Student because the check has to happen
    # before anyone is enrolled.
    residential_address = models.CharField(max_length=255, blank=True)
    residential_suburb = models.CharField(max_length=100, blank=True)
    residential_postcode = models.CharField(max_length=10, blank=True)
    campus = models.ForeignKey(
        "cyed_org.Campus", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="applications",
    )
    # Rank within the waitlist for a year level. Null unless waitlisted.
    waitlist_rank = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "cyed_admissions_applications"
        ordering = ["-created_at"]

    def applicant_name(self) -> str:
        return f"{self.applicant_first_name} {self.applicant_last_name}".strip()

    def __str__(self):
        return f"{self.applicant_first_name} {self.applicant_last_name} ({self.status})"


class ApplicationDocument(BaseModel):
    """
    One item on the admissions document checklist.

    `intake` already does OCR on uploads, but nothing bound a document to an
    application, so there was no "birth certificate received" state and no way
    to see what an application was still waiting on. A registrar chasing
    paperwork was doing it from memory.
    """

    KIND_CHOICES = [
        ("birth_certificate", "Birth certificate"),
        ("immunisation_statement", "AIR immunisation history statement"),
        ("proof_of_address", "Proof of address"),
        ("previous_reports", "Previous school reports"),
        ("visa_passport", "Visa / passport"),
        ("court_orders", "Court orders / parenting plan"),
        ("medical_plan", "Medical or action plan"),
        ("other", "Other"),
    ]
    # Without these an enrolment cannot be completed lawfully.
    REQUIRED_KINDS = {"birth_certificate", "immunisation_statement", "proof_of_address"}

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="documents"
    )
    kind = models.CharField(max_length=40, choices=KIND_CHOICES, default="other")
    is_received = models.BooleanField(default=False)
    received_on = models.DateField(null=True, blank=True)
    received_by = models.CharField(max_length=255, blank=True)
    document_ref = models.CharField(max_length=255, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_admissions_documents"
        ordering = ["kind"]
        constraints = [
            models.UniqueConstraint(
                fields=["application", "kind"], name="uniq_document_kind_per_application"
            ),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} ({'received' if self.is_received else 'outstanding'})"


class Offer(BaseModel):
    RESPONSE_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="offers")
    offered_year_level = models.PositiveSmallIntegerField(default=7)
    offer_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    response = models.CharField(max_length=20, choices=RESPONSE_CHOICES, default="pending")
    conditions = models.TextField(blank=True)
    # Who responded and when. An offer record with no response date cannot
    # settle a dispute about whether a family replied before it lapsed.
    responded_on = models.DateTimeField(null=True, blank=True)
    responded_by = models.CharField(max_length=255, blank=True)
    decline_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_admissions_offers"
        ordering = ["-created_at"]

    def has_expired(self, as_at=None) -> bool:
        """
        An offer past its expiry that nobody answered.

        Only meaningful while the response is still pending: a family who
        accepted on the last day does not lose their place because the date
        has since passed.
        """
        if self.response != "pending" or self.expiry_date is None:
            return False
        return (as_at or timezone.localdate()) > self.expiry_date

    def __str__(self):
        return f"Offer {self.application_id} → Y{self.offered_year_level} ({self.response})"
