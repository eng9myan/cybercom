from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class SchoolProfile(BaseModel):
    """
    Per-tenant school branding + identity. One profile per tenant; its name and
    logo appear on report cards and other official documents.
    """

    name = models.CharField(max_length=255, default="Your School")
    short_name = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=500, blank=True)
    suburb = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=20, blank=True)
    postcode = models.CharField(max_length=10, blank=True)
    principal_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    # Logo stored inline (small file) — JPEG is embeddable in the report PDF.
    logo_bytes = models.BinaryField(null=True, blank=True)
    logo_content_type = models.CharField(max_length=50, blank=True)

    # ── Report-card design (per-school) ──────────────────────────────────────
    report_title = models.CharField(max_length=120, default="Student Report Card")
    report_accent_color = models.CharField(max_length=7, default="#0EA5A4")  # hex
    report_show_logo = models.BooleanField(default=True)
    report_show_effort = models.BooleanField(default=True)
    report_show_general_comment = models.BooleanField(default=True)
    report_footer = models.CharField(max_length=255, blank=True)

    def report_design(self) -> dict:
        return {
            "title": self.report_title,
            "accent_color": self.report_accent_color,
            "show_logo": self.report_show_logo,
            "show_effort": self.report_show_effort,
            "show_general_comment": self.report_show_general_comment,
            "footer": self.report_footer,
        }

    class Meta:
        db_table = "cyed_school_profiles"
        constraints = [
            models.UniqueConstraint(fields=["tenant_id"], name="uniq_school_profile_per_tenant")
        ]

    @property
    def has_logo(self) -> bool:
        return bool(self.logo_bytes)

    def __str__(self):
        return self.name


def get_profile(tenant_id) -> "SchoolProfile":
    obj, _ = SchoolProfile.objects.get_or_create(tenant_id=tenant_id)
    return obj


class Notice(BaseModel):
    """
    A daily notice: what gets read out at assembly and shown on the portal.

    Every school has this board and CyEd had nowhere for it, so "no hats at
    lunch, Year 9 excursion money due Friday" lived in an email nobody kept.

    Two properties make it usable rather than another inbox:

    **It expires.** A notice runs between two dates and then stops appearing.
    A board that only ever grows is one nobody reads by week three, which is
    the failure mode of every noticeboard that has no end date.

    **It is addressed.** A notice for Year 9 should not fill a Year 7 student's
    screen. Audience and year level narrow it; empty means everyone.
    """

    AUDIENCE_CHOICES = [
        ("all", "Everyone"),
        ("staff", "Staff"),
        ("students", "Students"),
        ("parents", "Parents"),
    ]
    PRIORITY_CHOICES = [
        ("normal", "Normal"),
        ("important", "Important"),
        ("urgent", "Urgent"),
    ]

    title = models.CharField(max_length=255)
    body = models.TextField()
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default="all")
    # Blank means every year level. Stored as a comma list because a notice
    # routinely targets "9, 10" and a join table for that is overbuilt.
    year_levels = models.CharField(
        max_length=100, blank=True, help_text="e.g. '9,10'. Blank means all year levels."
    )
    campus = models.ForeignKey(
        "cyed_org.Campus", on_delete=models.CASCADE, null=True, blank=True,
        related_name="notices",
    )
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="normal")
    starts_on = models.DateField(default=timezone.localdate)
    # Inclusive. Null means it runs until someone takes it down — used sparingly,
    # and the reason `active_on` still checks `is_published`.
    ends_on = models.DateField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    posted_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_notices"
        ordering = ["-priority", "-starts_on"]
        indexes = [
            models.Index(fields=["tenant_id", "starts_on", "ends_on"], name="idx_notice_window"),
        ]

    def is_active(self, on=None) -> bool:
        on = on or timezone.localdate()
        if not self.is_published or self.starts_on > on:
            return False
        return self.ends_on is None or self.ends_on >= on

    def applies_to_year(self, year_level) -> bool:
        if not self.year_levels.strip():
            return True
        wanted = {y.strip() for y in self.year_levels.split(",") if y.strip()}
        return str(year_level) in wanted

    def __str__(self):
        return self.title
