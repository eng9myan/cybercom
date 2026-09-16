from datetime import date, timedelta

from django.db import models
from django.utils import timezone

from core.crypto import EncryptedTextField
from platform.common.models import BaseModel

# Diseases on the National Immunisation Program that a school is asked about at
# enrolment and during an outbreak. Keyed by disease rather than by vaccine
# brand: a school excluding children during a measles outbreak cares who is
# protected against measles, not which of MMR or MMRV delivered it.
VACCINE_PREVENTABLE = [
    ("measles", "Measles"),
    ("mumps", "Mumps"),
    ("rubella", "Rubella"),
    ("pertussis", "Whooping cough (pertussis)"),
    ("diphtheria", "Diphtheria"),
    ("tetanus", "Tetanus"),
    ("polio", "Poliomyelitis"),
    ("hepatitis_b", "Hepatitis B"),
    ("hib", "Haemophilus influenzae type b"),
    ("pneumococcal", "Pneumococcal"),
    ("meningococcal", "Meningococcal"),
    ("varicella", "Chickenpox (varicella)"),
    ("rotavirus", "Rotavirus"),
    ("hpv", "Human papillomavirus"),
]


class HealthRecord(BaseModel):
    student = models.OneToOneField("cyed_sis.Student", on_delete=models.CASCADE, related_name="health_record")
    blood_type = models.CharField(max_length=5, blank=True)
    # Sensitive medical PII — encrypted at rest (see core.crypto).
    allergies = EncryptedTextField(blank=True)
    conditions = EncryptedTextField(blank=True)
    medications = EncryptedTextField(blank=True)
    dietary_requirements = models.CharField(max_length=255, blank=True)
    emergency_contact = models.CharField(max_length=255, blank=True)
    medicare_number = EncryptedTextField(blank=True)
    notes = EncryptedTextField(blank=True)

    class Meta:
        db_table = "cyed_health_records"
        ordering = ["-created_at"]

    def __str__(self):
        return f"HealthRecord({self.student_id})"


class ActionPlan(BaseModel):
    """
    A student's emergency medical plan — anaphylaxis, asthma, diabetes, seizure.

    The document a teacher needs in ninety seconds, on a phone, possibly in a
    car park during an evacuation. CyEd could record that a child *has* an
    allergy but had nowhere to put what to actually do about it, which is the
    part that matters when it happens.

    Two decisions follow from that:

    **Plans expire and must be chased.** An ASCIA action plan is signed by a
    doctor and reviewed annually; an out-of-date plan is a real compliance
    finding and, worse, may describe the wrong dose. Expiry is tracked and
    surfaced the same way staff clearances are.

    **The instructions are not encrypted.** Everything else in this app is —
    but a plan that cannot be read without a working key, during an emergency,
    on a device with patchy signal, is a plan that fails when it is needed.
    Access is still restricted and audited; the trade is deliberate and is the
    same one paper plans on a staffroom wall make.
    """

    PLAN_TYPES = [
        ("anaphylaxis", "Anaphylaxis"),
        ("asthma", "Asthma"),
        ("diabetes", "Diabetes"),
        ("seizure", "Seizure / epilepsy"),
        ("allergy", "Allergy (non-anaphylactic)"),
        ("other", "Other"),
    ]
    SEVERITY = [
        ("critical", "Critical — life-threatening"),
        ("high", "High"),
        ("moderate", "Moderate"),
    ]
    # Plans whose absence or expiry should block an excursion and appear on the
    # emergency roll. Anaphylaxis and asthma are the two that kill children in
    # Australian schools.
    CRITICAL_TYPES = {"anaphylaxis", "asthma", "seizure", "diabetes"}

    student = models.ForeignKey(
        "cyed_sis.Student", on_delete=models.CASCADE, related_name="action_plans"
    )
    plan_type = models.CharField(max_length=30, choices=PLAN_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY, default="high")
    # What the child reacts to, in plain words. "Peanuts, tree nuts, sesame."
    triggers = models.CharField(max_length=500, blank=True)
    # The steps, verbatim from the signed plan. Deliberately unencrypted — see
    # the class docstring.
    emergency_steps = models.TextField(
        help_text="What to do, in order. Read aloud in an emergency — keep it plain."
    )
    medication = models.CharField(
        max_length=255, blank=True,
        help_text="e.g. 'EpiPen Jr 150mcg — in the front office fridge, red box'",
    )
    medication_location = models.CharField(max_length=255, blank=True)

    prescriber_name = models.CharField(max_length=255, blank=True)
    signed_on = models.DateField(null=True, blank=True)
    # ASCIA plans are reviewed annually; this is the date it stops being valid.
    review_due = models.DateField(null=True, blank=True)
    document_ref = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_health_action_plans"
        ordering = ["student", "plan_type"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "student", "plan_type"],
                name="uniq_action_plan_per_student_type",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant_id", "review_due"], name="idx_action_plan_review"),
        ]

    # Plans inside this window are surfaced for renewal — long enough to get a
    # GP appointment, which is the actual constraint on renewing one.
    REVIEW_WARNING_DAYS = 60

    def status(self, as_at: date | None = None) -> str:
        as_at = as_at or timezone.localdate()
        if not self.is_active:
            return "inactive"
        if self.review_due is None:
            return "no_review_date"
        if self.review_due < as_at:
            return "expired"
        if self.review_due <= as_at + timedelta(days=self.REVIEW_WARNING_DAYS):
            return "due_for_review"
        return "current"

    def is_current(self, as_at: date | None = None) -> bool:
        return self.status(as_at) in ("current", "due_for_review", "no_review_date")

    def __str__(self):
        return f"{self.get_plan_type_display()} plan for {self.student_id}"


class ImmunisationRecord(BaseModel):
    """
    A student's immunisation status, as evidenced at enrolment.

    Australian enrolment requires an Australian Immunisation Register
    Immunisation History Statement, and during an outbreak of a
    vaccine-preventable disease a public-health directive can require
    unimmunised children to be excluded from the school. Neither is possible
    without this record — CyEd previously had nowhere to put it.

    `status` is what the school can *evidence*, not what a parent said on the
    phone. `not_provided` is the honest default: a child whose statement has
    never been sighted is in exactly the same position, for exclusion purposes,
    as one known to be unimmunised.
    """

    STATUS_CHOICES = [
        ("up_to_date", "Up to date for age"),
        ("catch_up", "On a documented catch-up schedule"),
        ("medical_exemption", "Medical exemption (GP certified)"),
        ("not_provided", "No statement provided"),
        ("not_immunised", "Not immunised"),
    ]
    # Statuses that satisfy an enrolment requirement. A catch-up schedule
    # counts — the child is being brought up to date under medical supervision.
    ACCEPTABLE_AT_ENROLMENT = {"up_to_date", "catch_up", "medical_exemption"}

    student = models.OneToOneField(
        "cyed_sis.Student", on_delete=models.CASCADE, related_name="immunisation"
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="not_provided")
    # Date of the AIR Immunisation History Statement that was sighted.
    air_statement_on = models.DateField(null=True, blank=True)
    document_ref = models.CharField(
        max_length=255, blank=True, help_text="Where the sighted statement is filed."
    )
    # Verification is a human act, like a clearance: someone sighted the
    # statement. A status with nobody behind it is not evidence.
    verified_by = models.CharField(max_length=255, blank=True)
    verified_on = models.DateField(null=True, blank=True)
    exemption_reason = EncryptedTextField(blank=True)
    notes = EncryptedTextField(blank=True)

    class Meta:
        db_table = "cyed_immunisation_records"
        ordering = ["-updated_at"]

    def is_acceptable_at_enrolment(self) -> bool:
        return self.status in self.ACCEPTABLE_AT_ENROLMENT and bool(self.verified_on)

    def protected_against(self, disease: str) -> bool:
        """
        Whether this child can be treated as protected against one disease.

        A medical exemption does *not* confer protection — an exempt child is
        precisely the one a public-health exclusion is designed to protect, so
        conflating "lawfully enrolled" with "safe during an outbreak" would
        invert the purpose of the register.
        """
        return self.doses.filter(disease=disease).exists()

    def __str__(self):
        return f"Immunisation({self.student_id}: {self.status})"


class ImmunisationDose(BaseModel):
    """One recorded dose protecting against one disease."""

    record = models.ForeignKey(
        ImmunisationRecord, on_delete=models.CASCADE, related_name="doses"
    )
    disease = models.CharField(max_length=30, choices=VACCINE_PREVENTABLE)
    vaccine_name = models.CharField(max_length=120, blank=True)  # e.g. "MMR II"
    dose_number = models.PositiveSmallIntegerField(default=1)
    given_on = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cyed_immunisation_doses"
        ordering = ["disease", "dose_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["record", "disease", "dose_number"],
                name="uniq_dose_per_disease_per_record",
            ),
        ]

    def __str__(self):
        return f"{self.get_disease_display()} dose {self.dose_number}"


class MedicationAuthority(BaseModel):
    """
    Standing authorisation to give a named student a named medication.

    A school may not administer prescribed medication on a teacher's judgement.
    There has to be a written authority — from the prescriber, consented to by
    the guardian — stating the drug, dose, route and timing. This model is that
    authority, and every dose in `MedicationAdministration` must point at one.

    Without it the administration log would record who gave what, but not
    whether they were ever permitted to.
    """

    ROUTE_CHOICES = [
        ("oral", "Oral"), ("inhaled", "Inhaled"), ("topical", "Topical"),
        ("injection", "Injection"), ("nasal", "Nasal"), ("other", "Other"),
    ]

    student = models.ForeignKey(
        "cyed_sis.Student", on_delete=models.CASCADE, related_name="medication_authorities"
    )
    medication_name = models.CharField(max_length=200)
    dose = models.CharField(max_length=100, help_text="e.g. '2 puffs', '5 mL', '1 tablet'")
    route = models.CharField(max_length=20, choices=ROUTE_CHOICES, default="oral")
    # Free text because real instructions are conditional ("before sport", "if
    # wheezing"). The machine-checkable limits are the two fields below.
    instructions = EncryptedTextField(blank=True)
    max_doses_per_day = models.PositiveSmallIntegerField(
        default=1, help_text="Hard ceiling enforced at administration time."
    )
    min_hours_between_doses = models.DecimalField(
        max_digits=4, decimal_places=1, default=0,
        help_text="Minimum interval; 0 disables the interval check.",
    )
    prescriber_name = models.CharField(max_length=255, blank=True)
    # The guardian who consented. Required in practice; nullable so an import
    # of historical paper authorities is not blocked by a missing link.
    authorised_by = models.ForeignKey(
        "cyed_sis.Guardian", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="medication_authorities",
    )
    consent_document_ref = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    # Asthma inhalers and adrenaline auto-injectors are commonly carried and
    # self-administered by the student under a documented plan.
    self_administer_permitted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_medication_authorities"
        ordering = ["student", "medication_name"]

    def is_current(self, as_at=None) -> bool:
        as_at = as_at or timezone.localdate()
        if not self.is_active:
            return False
        if self.start_date and as_at < self.start_date:
            return False
        if self.end_date and as_at > self.end_date:
            return False
        return True

    def doses_given_on(self, day):
        return self.administrations.filter(administered_on=day, outcome="given").count()

    def last_dose_before(self, when):
        return self.administrations.filter(
            outcome="given", administered_at__lt=when
        ).order_by("-administered_at").first()

    def __str__(self):
        return f"{self.medication_name} for {self.student_id}"


class MedicationAdministration(BaseModel):
    """
    One dose event: what was given, to whom, by whom, and when.

    A school administering prescribed medication must record each dose. This is
    a duty-of-care record, not an activity log — it is the document produced
    when a parent, a regulator or a coroner asks what happened, so it records
    refusals and missed doses as first-class outcomes rather than only
    successes. A dose that was *not* given is often the fact that matters.
    """

    OUTCOME_CHOICES = [
        ("given", "Given"),
        ("refused", "Refused by student"),
        ("omitted", "Not given"),
    ]

    authority = models.ForeignKey(
        MedicationAuthority, on_delete=models.PROTECT, related_name="administrations"
    )
    student = models.ForeignKey(
        "cyed_sis.Student", on_delete=models.CASCADE, related_name="medication_administrations"
    )
    administered_at = models.DateTimeField()
    # Denormalised for the daily count and the per-day uniqueness of a log
    # page; derived from `administered_at` on save.
    administered_on = models.DateField()
    dose_given = models.CharField(max_length=100)
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, default="given")
    # Who physically gave it. Not free text: "the office" is not accountable,
    # a named staff member is.
    administered_by = models.ForeignKey(
        "cyed_hr.Staff", on_delete=models.PROTECT, related_name="medications_administered"
    )
    # Best practice for scheduled medication in schools is a second signature.
    witnessed_by = models.ForeignKey(
        "cyed_hr.Staff", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="medications_witnessed",
    )
    self_administered = models.BooleanField(
        default=False, help_text="Student took it themselves under supervision."
    )
    notes = EncryptedTextField(blank=True)
    # Populated when leadership knowingly records a dose outside the authority's
    # limits — the same pattern as a leave-balance override.
    limit_override_by = models.CharField(max_length=255, blank=True)
    limit_override_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_medication_administrations"
        ordering = ["-administered_at"]
        indexes = [
            models.Index(
                fields=["tenant_id", "student", "administered_on"],
                name="idx_medadmin_student_day",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.administered_at and not self.administered_on:
            self.administered_on = timezone.localtime(self.administered_at).date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.authority_id} {self.outcome} at {self.administered_at}"


class MedicalIncident(BaseModel):
    student = models.ForeignKey("cyed_sis.Student", on_delete=models.CASCADE, related_name="medical_incidents")
    date = models.DateField(null=True, blank=True)
    description = EncryptedTextField(blank=True)
    treatment = EncryptedTextField(blank=True)
    administered_by = models.CharField(max_length=255, blank=True)
    medication_given = models.CharField(max_length=255, blank=True)
    parent_notified = models.BooleanField(default=False)
    sent_home = models.BooleanField(default=False)

    class Meta:
        db_table = "cyed_medical_incidents"
        ordering = ["-date"]

    def __str__(self):
        return f"Incident({self.student_id} · {self.date})"


class SickBayVisit(BaseModel):
    """
    A student's visit to the sick bay, from arrival to outcome.

    `MedicalIncident` recorded that something happened; it could not answer the
    two questions a first-aid officer is actually asked during the day — *who
    is in the sick bay right now*, and *has anyone rung that child's parents*.
    `parent_notified` was a boolean somebody had to remember to tick after
    making the call themselves.

    Design points that matter:

    **A visit is open until it is closed.** `departed_at` being null is what
    makes "who is here now" answerable, and it is the same mechanism the
    emergency roll needs — a child lying down in the sick bay during an
    evacuation is exactly the one nobody thinks to look for.

    **Notification is a consequence of the outcome, not a checkbox.** Choosing
    "send home" or "emergency" sends the guardians a message through the same
    delivery path as every other alert, and records what was actually sent. A
    tickbox saying a parent was told, with nothing behind it, is the defect
    this replaces.
    """

    OUTCOME_CHOICES = [
        ("in_progress", "Still in the sick bay"),
        ("returned_to_class", "Returned to class"),
        ("sent_home", "Collected by a guardian"),
        ("emergency", "Emergency services called"),
    ]
    # Outcomes that mean somebody has to be told now, not in the daily digest.
    NOTIFY_OUTCOMES = {"sent_home", "emergency"}

    student = models.ForeignKey(
        "cyed_sis.Student", on_delete=models.CASCADE, related_name="sick_bay_visits"
    )
    arrived_at = models.DateTimeField(default=timezone.now)
    departed_at = models.DateTimeField(null=True, blank=True)
    # Where they came from, so a teacher can be told the child is safe.
    referred_by = models.CharField(max_length=255, blank=True)
    complaint = EncryptedTextField(blank=True)
    observations = EncryptedTextField(blank=True)
    treatment = EncryptedTextField(blank=True)
    # Set when the visit is closed.
    outcome = models.CharField(max_length=30, choices=OUTCOME_CHOICES, default="in_progress")
    seen_by = models.ForeignKey(
        "cyed_hr.Staff", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="sick_bay_visits",
    )
    # Links a dose given here to the medication log, so the same event is not
    # recorded twice in two places that then disagree.
    medication_given = models.ForeignKey(
        "MedicationAdministration", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="sick_bay_visits",
    )
    collected_by = models.CharField(max_length=255, blank=True)
    guardians_notified = models.PositiveSmallIntegerField(default=0)
    notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cyed_sick_bay_visits"
        ordering = ["-arrived_at"]
        indexes = [
            models.Index(
                fields=["tenant_id", "departed_at"], name="idx_sickbay_open"
            ),
        ]

    def is_open(self) -> bool:
        return self.departed_at is None

    def minutes_present(self, as_at=None) -> int:
        end = self.departed_at or (as_at or timezone.now())
        return max(0, int((end - self.arrived_at).total_seconds() // 60))

    def __str__(self):
        return f"Sick bay: {self.student_id} at {self.arrived_at:%H:%M} ({self.outcome})"
