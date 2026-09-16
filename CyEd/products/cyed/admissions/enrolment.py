"""
Admissions: catchment, offers, and the post-enrolment chain.

The audit's finding was that `enrol` created a bare Student and stopped. It did
not attach the family, assign a fee plan, allocate a class, or trigger consent
forms — so everything an offer *implies* was manual re-keying, which is most of
what a registrar's day consists of.

`enrol_application` does the whole chain in one transaction and reports what it
created. The pieces are deliberately individually skippable: a school that
allocates classes in a separate exercise in January should not be forced to
pick one in October, and a missing fee plan should not block the enrolment of a
child. Anything skipped is named in the report rather than silently omitted —
a registrar needs to know what is still outstanding, which is precisely the
information a silent success destroys.

Household attachment is the piece that pays for itself: matching the guardian's
email to an existing household is what makes a second child a *sibling*, which
is what makes the sibling discount fire without anyone remembering to apply it.
"""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from products.cyed.admissions.models import (
    Application,
    ApplicationDocument,
    CatchmentZone,
    Offer,
)


class AdmissionsError(Exception):
    """An admissions action was refused for a business reason (→ HTTP 400/409)."""


# ── catchment ────────────────────────────────────────────────────────────────
def catchment_check(tenant_id, *, suburb="", postcode="", campus_id=None) -> dict:
    """
    Which zone, if any, an address falls into.

    Returns a verdict rather than raising: being out of zone is a fact a
    registrar weighs, not automatically a refusal. Most schools can enrol out
    of zone when there is room, and a system that hard-blocked it would simply
    be worked around.
    """
    zones = CatchmentZone.objects.filter(tenant_id=tenant_id, is_active=True)
    if campus_id:
        zones = zones.filter(campus_id__in=[campus_id, None])

    if not zones.exists():
        return {
            "checked": False, "in_catchment": None, "zone": None, "is_priority": False,
            "reason": "No catchment zones are configured, so no boundary could be checked.",
        }
    if not (suburb or postcode):
        return {
            "checked": False, "in_catchment": None, "zone": None, "is_priority": False,
            "reason": "No residential suburb or postcode on the application.",
        }

    matches = [z for z in zones if z.covers(suburb=suburb, postcode=postcode)]
    if not matches:
        return {
            "checked": True, "in_catchment": False, "zone": None, "is_priority": False,
            "reason": f"{suburb or postcode} is not in any configured zone.",
        }
    # A priority zone beats a general one when an address falls in both.
    best = sorted(matches, key=lambda z: (not z.is_priority, z.name))[0]
    return {
        "checked": True, "in_catchment": True, "zone": str(best.id),
        "zone_name": best.name, "is_priority": best.is_priority, "reason": "",
    }


def check_application_catchment(application) -> dict:
    return catchment_check(
        application.tenant_id,
        suburb=application.residential_suburb,
        postcode=application.residential_postcode,
        campus_id=application.campus_id,
    )


# ── documents ────────────────────────────────────────────────────────────────
def ensure_document_checklist(application):
    """Create the standard checklist. Idempotent — re-running never duplicates."""
    existing = set(application.documents.values_list("kind", flat=True))
    created = [
        ApplicationDocument.objects.create(
            tenant_id=application.tenant_id, application=application, kind=kind
        )
        for kind in ApplicationDocument.REQUIRED_KINDS
        if kind not in existing
    ]
    return created


def outstanding_documents(application):
    return list(
        application.documents.filter(is_received=False).values_list("kind", flat=True)
    )


# ── offers ───────────────────────────────────────────────────────────────────
def respond_to_offer(offer, *, response, responded_by="", decline_reason=""):
    """
    A family accepts or declines. This is the step that did not exist: offers
    were recorded but had no parent-facing decision, no expiry and no waitlist
    consequence.
    """
    if response not in ("accepted", "declined"):
        raise AdmissionsError("A response must be 'accepted' or 'declined'.")
    if offer.response != "pending":
        raise AdmissionsError(f"This offer was already {offer.response}.")
    if offer.has_expired():
        raise AdmissionsError(
            f"This offer expired on {offer.expiry_date}. Reissue it if the place is still open."
        )

    offer.response = response
    offer.responded_on = timezone.now()
    offer.responded_by = responded_by[:255]
    offer.decline_reason = decline_reason[:255] if response == "declined" else ""
    offer.save(update_fields=[
        "response", "responded_on", "responded_by", "decline_reason", "updated_at",
    ])

    application = offer.application
    application.status = response
    application.save(update_fields=["status", "updated_at"])
    return offer


def lapse_expired_offers(tenant_id, as_at=None):
    """
    Mark unanswered offers past their expiry as declined, freeing the place.

    Run daily. Without it an offer nobody answered holds a place open forever
    and the waitlist behind it never moves — the failure mode is invisible,
    because nothing looks broken.
    """
    as_at = as_at or timezone.localdate()
    lapsed = []
    for offer in Offer.objects.select_related("application").filter(
        tenant_id=tenant_id, response="pending", expiry_date__lt=as_at
    ):
        offer.response = "declined"
        offer.responded_on = timezone.now()
        offer.decline_reason = "Offer lapsed — no response by the expiry date."
        offer.save(update_fields=[
            "response", "responded_on", "decline_reason", "updated_at",
        ])
        offer.application.status = "declined"
        offer.application.save(update_fields=["status", "updated_at"])
        lapsed.append(offer)
    return lapsed


def waitlist(tenant_id, *, year_level=None, campus_id=None):
    """The queue for a year level, in rank order."""
    qs = Application.objects.filter(tenant_id=tenant_id, status="waitlisted")
    if year_level:
        qs = qs.filter(year_level_applying=year_level)
    if campus_id:
        qs = qs.filter(campus_id=campus_id)
    return qs.order_by("waitlist_rank", "created_at")


def add_to_waitlist(application, *, rank=None):
    """
    Put an application in the queue. Rank defaults to the end of the queue for
    that year level, so ordering is by when they applied unless someone
    deliberately reorders it.
    """
    if rank is None:
        last = (
            Application.objects.filter(
                tenant_id=application.tenant_id, status="waitlisted",
                year_level_applying=application.year_level_applying,
            ).order_by("-waitlist_rank").first()
        )
        rank = (last.waitlist_rank or 0) + 1 if last else 1
    application.status = "waitlisted"
    application.waitlist_rank = rank
    application.save(update_fields=["status", "waitlist_rank", "updated_at"])
    return application


# ── the enrolment chain ──────────────────────────────────────────────────────
def _link_guardian(application, student):
    """
    Attach the applying guardian, reusing an existing record when the email
    matches. Reuse is the point: it is what turns a second child into a sibling
    rather than a stranger who happens to share a surname.
    """
    from products.cyed.sis.models import Guardian

    email = (application.guardian_email or "").strip()
    name = (application.guardian_name or "").strip()
    if not email and not name:
        return None, False

    guardian = None
    if email:
        guardian = Guardian.objects.filter(
            tenant_id=application.tenant_id, email__iexact=email
        ).first()

    created = False
    if guardian is None:
        first, _, last = name.partition(" ")
        guardian = Guardian.objects.create(
            tenant_id=application.tenant_id,
            first_name=first or name or "Guardian",
            last_name=last or application.applicant_last_name,
            email=email,
            phone=application.guardian_phone or "",
        )
        created = True

    guardian.students.add(student)
    return guardian, created


def _link_family(application, student, guardian, explicit_family=None):
    """
    Put the child in a household — the existing one if their guardian already
    has children here.
    """
    from products.cyed.sis.models import Family

    family = explicit_family
    if family is None and guardian is not None:
        family = guardian.family
    if family is None and guardian is not None:
        # A sibling already enrolled under the same guardian implies the household.
        sibling = guardian.students.exclude(id=student.id).filter(
            family__isnull=False
        ).first()
        if sibling is not None:
            family = sibling.family

    created = False
    if family is None:
        family = Family.objects.create(
            tenant_id=application.tenant_id,
            name=f"{application.applicant_last_name} Household",
            address_line1=application.residential_address or "",
            suburb=application.residential_suburb or "",
            postcode=application.residential_postcode or "",
            primary_contact_email=(application.guardian_email or ""),
            primary_contact_phone=(application.guardian_phone or ""),
            billing_contact=guardian,
        )
        created = True

    student.family = family
    student.save(update_fields=["family", "updated_at"])
    if guardian is not None and guardian.family_id is None:
        guardian.family = family
        guardian.save(update_fields=["family", "updated_at"])
    return family, created


def _assign_fee_plan(application, student, *, fee_plan, academic_year=None):
    """
    Create the bill and its installment schedule.

    Tuition comes from the `FeeSchedule` for the child's year level. The
    sibling discount is applied automatically by `billing.services`, because
    the household was attached first — the ordering of this chain is load
    bearing, not incidental.
    """
    from products.cyed.billing.models import BillLineItem, StudentBill
    from products.cyed.billing.services import generate_installments
    from products.cyed.fees.models import FeeSchedule

    schedule = FeeSchedule.objects.filter(
        tenant_id=application.tenant_id, is_active=True,
        applies_to_year_level=student.year_level,
    ).order_by("-created_at").first()
    if schedule is None:
        return None, "No active fee schedule for this year level."

    bill = StudentBill.objects.create(
        tenant_id=application.tenant_id, student=student, plan=fee_plan,
        academic_year=academic_year, campus=application.campus, status="draft",
        start_date=timezone.localdate(),
    )
    BillLineItem.objects.create(
        tenant_id=application.tenant_id, bill=bill, category="tuition",
        description=schedule.name, amount=Decimal(schedule.amount),
    )
    generate_installments(bill)
    return bill, ""


def _allocate_class(application, student, class_section):
    """Place the child in a class, refusing to overfill it."""
    from products.cyed.sis.models import Enrolment

    active = Enrolment.objects.filter(
        tenant_id=application.tenant_id, class_section=class_section, status="active"
    ).count()
    if class_section.capacity and active >= class_section.capacity:
        return None, (
            f"{class_section.name} is full ({active}/{class_section.capacity}). "
            f"Allocate the student to another section."
        )
    enrolment = Enrolment.objects.create(
        tenant_id=application.tenant_id, student=student, class_section=class_section,
        status="active", enrolled_on=timezone.localdate(),
    )
    return enrolment, ""


def _open_immunisation_record(application, student):
    """
    Create the immunisation record up front, as `not_provided`.

    Deliberate: an absent record and an unimmunised child are the same thing
    for exclusion purposes, so creating the row makes the child visible in the
    immunisation gap list from day one instead of being invisible until someone
    thinks to ask.
    """
    from products.cyed.health.models import ImmunisationRecord

    record, created = ImmunisationRecord.objects.get_or_create(
        tenant_id=application.tenant_id, student=student,
        defaults={"status": "not_provided"},
    )
    return record, created


@transaction.atomic
def enrol_application(
    application, *, fee_plan=None, class_section=None, family=None,
    academic_year=None, campus=None, require_documents=True, actor="",
):
    """
    Turn an accepted application into a fully set-up student.

    Returns a report naming everything created *and everything skipped* — the
    outstanding list is the useful half. Runs in one transaction: a chain that
    half-completed would leave a child enrolled with no household and no bill,
    which is worse than not starting.
    """
    from products.cyed.sis.models import Student

    if application.enrolled_student_id:
        raise AdmissionsError("This application has already been enrolled.")
    if application.status in ("declined", "withdrawn"):
        raise AdmissionsError(f"A {application.status} application cannot be enrolled.")

    if require_documents:
        outstanding = outstanding_documents(application)
        if outstanding:
            raise AdmissionsError(
                "Required documents are outstanding: "
                + ", ".join(sorted(outstanding))
                + ". Enrol with require_documents=false to proceed anyway."
            )

    if campus is None:
        campus = application.campus

    student = Student.objects.create(
        tenant_id=application.tenant_id,
        first_name=application.applicant_first_name,
        last_name=application.applicant_last_name,
        date_of_birth=application.date_of_birth,
        year_level=application.year_level_applying,
        enrolment_status="enrolled",
        campus=campus,
    )
    # The residential address lives on the household, not the child — siblings
    # share one, and duplicating it per student is how the two drift apart.

    report = {
        "student": str(student.id),
        "name": student.first_name + " " + student.last_name,
        "created": [],
        "skipped": [],
        "catchment": check_application_catchment(application),
    }

    guardian, guardian_created = _link_guardian(application, student)
    if guardian is None:
        report["skipped"].append({
            "step": "guardian",
            "reason": "The application has no guardian name or email.",
        })
    else:
        report["created"].append({
            "step": "guardian", "id": str(guardian.id),
            "detail": "created" if guardian_created else "linked existing",
        })

    household, family_created = _link_family(application, student, guardian, explicit_family=family)
    report["created"].append({
        "step": "family", "id": str(household.id),
        "detail": "created" if family_created else "joined existing household",
    })

    if fee_plan is None:
        report["skipped"].append({
            "step": "billing", "reason": "No fee plan was supplied."
        })
    else:
        bill, problem = _assign_fee_plan(
            application, student, fee_plan=fee_plan, academic_year=academic_year
        )
        if bill is None:
            report["skipped"].append({"step": "billing", "reason": problem})
        else:
            report["created"].append({
                "step": "billing", "id": str(bill.id),
                "detail": f"{bill.installments.count()} installment(s), "
                          f"{bill.balance} due",
            })

    if class_section is None:
        report["skipped"].append({
            "step": "class_allocation", "reason": "No class section was supplied."
        })
    else:
        enrolment, problem = _allocate_class(application, student, class_section)
        if enrolment is None:
            # A full class is a real refusal, not a silent skip — raising rolls
            # the whole chain back so nobody is half-enrolled into a full room.
            raise AdmissionsError(problem)
        report["created"].append({
            "step": "class_allocation", "id": str(enrolment.id),
            "detail": class_section.name,
        })

    _record, immunisation_created = _open_immunisation_record(application, student)
    report["created"].append({
        "step": "immunisation_record",
        "detail": "opened as not_provided" if immunisation_created else "already existed",
    })

    application.enrolled_student_id = student.id
    application.status = "enrolled"
    application.save(update_fields=["enrolled_student_id", "status", "updated_at"])

    return student, report
