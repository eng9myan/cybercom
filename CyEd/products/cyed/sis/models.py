from django.db import models
from django.db.models import F

from platform.common.models import BaseModel


class AcademicYear(BaseModel):
    name = models.CharField(max_length=50)  # e.g. "2026"
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        db_table = "cyed_academic_years"
        ordering = ["-name"]

    def __str__(self):
        return self.name


class Guardian(BaseModel):
    RELATIONSHIP_CHOICES = [
        ("mother", "Mother"),
        ("father", "Father"),
        ("grandparent", "Grandparent"),
        ("carer", "Carer"),
        ("other", "Other"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES, default="other")
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    is_primary_contact = models.BooleanField(default=False)
    # Household this guardian belongs to. Nullable: guardians existed before
    # families did, and a guardian may be linked to children without one.
    family = models.ForeignKey(
        "Family", on_delete=models.SET_NULL, null=True, blank=True, related_name="guardians"
    )

    class Meta:
        db_table = "cyed_guardians"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Family(BaseModel):
    """
    A household — the unit a school actually bills.

    Students link here by a NULLABLE FK (pre-existing rows survive untouched)
    and Guardians do too. The Student↔Guardian M2M is deliberately left alone:
    it answers "who may collect / be contacted about this child", which is a
    different question from "who pays". A blended household can therefore have
    guardians attached to some children and not others while still receiving a
    single consolidated statement.

    Sibling discounts, consolidated invoices and family statements all hang off
    this model; see products/cyed/billing/family_accounts.py.
    """

    name = models.CharField(max_length=200)  # e.g. "Nguyen–Patel Household"
    primary_contact_email = models.EmailField(blank=True)
    primary_contact_phone = models.CharField(max_length=50, blank=True)
    # The guardian invoices are addressed to. SET_NULL so removing a guardian
    # never orphans the household's financial history.
    billing_contact = models.ForeignKey(
        Guardian,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="billing_for_families",
    )
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    suburb = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    postcode = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default="Australia")
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_families"
        ordering = ["name"]

    # ── Sibling ordering ─────────────────────────────────────────────────────
    # "Eldest first" must be deterministic, because the sibling-discount ordinal
    # is derived from position in this list and a school has to be able to
    # explain to a parent exactly which child got which discount.
    ORDERING = ("-year_level", F("date_of_birth").asc(nulls_last=True), "id")

    def students_ordered(self):
        """Every child in the household, eldest first (see ORDERING)."""
        return self.students.order_by(*self.ORDERING)

    def students_enrolled(self):
        """
        ENROLLED children only, eldest first.

        Sibling ordinals come from this queryset, so a withdrawn or graduated
        child never occupies an ordinal and therefore cannot keep inflating a
        younger sibling's discount.
        """
        return self.students.filter(enrolment_status="enrolled").order_by(*self.ORDERING)

    def billing_email(self) -> str:
        if self.billing_contact and self.billing_contact.email:
            return self.billing_contact.email
        return self.primary_contact_email

    def postal_address(self) -> str:
        parts = [self.address_line1, self.address_line2, self.suburb, self.state,
                 self.postcode, self.country]
        return ", ".join(p for p in parts if p)

    def __str__(self):
        return self.name


class Student(BaseModel):
    STATUS_CHOICES = [
        ("enrolled", "Enrolled"),
        ("applicant", "Applicant"),
        ("graduated", "Graduated"),
        ("withdrawn", "Withdrawn"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    student_number = models.CharField(max_length=50, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=30, blank=True)
    year_level = models.PositiveSmallIntegerField(default=7)  # F–12; F stored as 0
    enrolment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="applicant")
    email = models.EmailField(blank=True)
    campus = models.ForeignKey("cyed_org.Campus", on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="students")
    guardians = models.ManyToManyField(Guardian, related_name="students", blank=True)
    # Billing household. NULLABLE on purpose: every Student row that predates
    # the family model keeps working, and an unallocated child is simply a
    # family of one for discount purposes.
    family = models.ForeignKey(
        Family, on_delete=models.SET_NULL, null=True, blank=True, related_name="students"
    )

    # ── AU statutory demographics (ACARA/ABS national data collections) ──────
    # ABS Indigenous Status Standard codes.
    INDIGENOUS_CHOICES = [
        ("1", "Aboriginal but not Torres Strait Islander"),
        ("2", "Torres Strait Islander but not Aboriginal"),
        ("3", "Both Aboriginal and Torres Strait Islander"),
        ("4", "Neither"),
        ("9", "Not stated / unknown"),
    ]
    usi = models.CharField(max_length=10, blank=True)  # Unique Student Identifier (national)
    state_student_number = models.CharField(max_length=30, blank=True)  # VSN/QSN/etc.
    indigenous_status = models.CharField(max_length=1, choices=INDIGENOUS_CHOICES, default="9")
    country_of_birth = models.CharField(max_length=100, blank=True)
    language_at_home = models.CharField(max_length=100, blank=True)
    lbote = models.BooleanField(default=False)  # Language Background Other Than English
    # ABS parental education/occupation codes drive the SES/census return.
    parent1_school_education = models.CharField(max_length=2, blank=True)  # 0/1/2 (highest year)
    parent1_occupation_group = models.CharField(max_length=2, blank=True)  # 1–4, 8, 9
    parent2_school_education = models.CharField(max_length=2, blank=True)
    parent2_occupation_group = models.CharField(max_length=2, blank=True)

    # ── exit ────────────────────────────────────────────────────────────────
    # Recorded so a leaver is more than a status change: alumni relations,
    # statutory returns and the Transfer Certificate all need to know when a
    # student left and where they went.
    exit_date = models.DateField(null=True, blank=True)
    exit_reason = models.CharField(max_length=255, blank=True)
    exit_destination = models.CharField(
        max_length=255, blank=True, help_text="Receiving school or destination, if known."
    )

    class Meta:
        db_table = "cyed_students"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} (Y{self.year_level})"


class TransferCertificate(BaseModel):
    """
    The document a receiving school asks for when a student moves.

    Versioned rather than editable, and carrying a frozen snapshot: a
    certificate reissued next year must still say what it said at the time,
    even if the student record has changed since. Reissuing mints a new version
    and keeps the old one.
    """

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="transfer_certificates"
    )
    version = models.PositiveSmallIntegerField(default=1)
    number = models.CharField(max_length=60)
    issued_on = models.DateField()
    issued_by = models.CharField(max_length=255, blank=True)
    # Frozen facts at the moment of issue — see lifecycle._certificate_snapshot.
    snapshot = models.JSONField(default=dict)
    fees_settled = models.BooleanField(default=False)
    notes = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "cyed_transfer_certificates"
        ordering = ["-issued_on", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "version"], name="uniq_tc_version_per_student"
            ),
        ]

    def __str__(self):
        return f"{self.number} (v{self.version})"


class CampusTransfer(BaseModel):
    """
    A student moving between campuses in the same school group.

    `Student.campus` was a bare FK that could be overwritten with no trace, so
    a mid-year move left no answer to "which campus was this child at in
    March?" — a question that matters for attendance returns, per-campus
    funding, and any incident that has to be attributed to a site.

    The row is the record. `Student.campus` is the *current* value derived from
    the latest effective transfer, which is why the transfer is written first
    and the student updated second.
    """

    student = models.ForeignKey(
        "cyed_sis.Student", on_delete=models.CASCADE, related_name="campus_transfers"
    )
    from_campus = models.ForeignKey(
        "cyed_org.Campus", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="transfers_out",
    )
    to_campus = models.ForeignKey(
        "cyed_org.Campus", on_delete=models.PROTECT, related_name="transfers_in"
    )
    effective_on = models.DateField()
    reason = models.CharField(max_length=255, blank=True)
    requested_by = models.CharField(max_length=255, blank=True)
    # Class placements do not follow a student across campuses; the old ones
    # are ended so the child stops appearing on a roll at a site they left.
    enrolments_ended = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "cyed_campus_transfers"
        ordering = ["-effective_on", "-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "student", "effective_on"],
                         name="idx_transfer_student_date"),
        ]

    def __str__(self):
        return f"{self.student_id}: {self.from_campus_id} → {self.to_campus_id} on {self.effective_on}"


class ClassSection(BaseModel):
    name = models.CharField(max_length=100)  # e.g. "8A Mathematics"
    subject = models.CharField(max_length=100, blank=True)
    year_level = models.PositiveSmallIntegerField(default=7)
    # DEPRECATED: free-text fallback, kept so pre-migration rows and any
    # not-yet-backfilled data still display something. New code should use
    # `teacher` (the real link to hr.Staff) instead. Do not read this field
    # to answer "who teaches this class" — see teacher_display().
    teacher_name = models.CharField(max_length=255, blank=True)
    # The actual teacher of record. Nullable: some sections (e.g. a study
    # hall) may have no assigned teacher, and rows created before this field
    # existed have not necessarily been backfilled yet.
    teacher = models.ForeignKey(
        "cyed_hr.Staff", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="class_sections",
    )
    room = models.CharField(max_length=50, blank=True)
    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.SET_NULL, null=True, blank=True, related_name="class_sections"
    )
    campus = models.ForeignKey("cyed_org.Campus", on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="class_sections")
    capacity = models.PositiveSmallIntegerField(default=30)

    class Meta:
        db_table = "cyed_class_sections"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def teacher_display(self) -> str:
        """Best available label for who teaches this class: the linked staff
        record if present, else the legacy free-text name."""
        if self.teacher_id:
            return f"{self.teacher.first_name} {self.teacher.last_name}".strip()
        return self.teacher_name


class Enrolment(BaseModel):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("dropped", "Dropped"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrolments")
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE, related_name="enrolments")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    enrolled_on = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cyed_enrolments"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "class_section"], name="uniq_student_class_section"
            )
        ]

    def __str__(self):
        return f"{self.student} → {self.class_section}"
