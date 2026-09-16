"""
Staff compliance and leave balances.

Two questions HR is asked more than any others, neither of which CyEd could
answer before this module existed:

    "Is this person's clearance current?"
    "Does she have leave left?"

Both are enforcement points, not report queries. An expired Working With
Children Check has to *stop* a classroom assignment, and a leave request that
exceeds the balance has to be refused or knowingly overridden — a system that
merely displays the problem has not met the obligation.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from products.cyed.hr.models import Contract, LeaveEntitlement, Staff, StaffClearance


class ComplianceError(Exception):
    """A staffing action was refused on compliance grounds (→ HTTP 400/409)."""


# ── clearances ───────────────────────────────────────────────────────────────
def clearance_state(staff, as_at: date | None = None) -> dict:
    """
    Every credential this person holds, and whether they may be in a classroom.

    A *missing* blocking credential is treated exactly like an expired one.
    Absence of evidence is not evidence of a clearance: a school that has never
    recorded a WWCC for someone is in the same position as one whose record
    lapsed, and the audit outcome is identical.
    """
    as_at = as_at or timezone.localdate()
    # Read through the related manager rather than querying the table directly,
    # so a caller that has `prefetch_related("clearances")` — the staff list
    # endpoint does — pays one query for the whole page instead of one per row.
    rows = list(staff.clearances.all())
    by_kind = {c.kind: c for c in rows}

    blocking = []
    for kind in sorted(StaffClearance.BLOCKING_KINDS):
        clearance = by_kind.get(kind)
        if clearance is None:
            blocking.append({"kind": kind, "reason": "missing", "expires_on": None})
        elif not clearance.is_current(as_at):
            blocking.append({
                "kind": kind,
                "reason": clearance.status(as_at),
                "expires_on": clearance.expires_on.isoformat() if clearance.expires_on else None,
            })

    return {
        "staff": str(staff.id),
        "name": f"{staff.first_name} {staff.last_name}".strip(),
        "may_teach": not blocking,
        "blocking": blocking,
        "clearances": [
            {
                "id": str(c.id),
                "kind": c.kind,
                "number": c.number,
                "issuing_state": c.issuing_state,
                "expires_on": c.expires_on.isoformat() if c.expires_on else None,
                "status": c.status(as_at),
                "days_until_expiry": c.days_until_expiry(as_at),
                "verified_on": c.verified_on.isoformat() if c.verified_on else None,
            }
            for c in rows
        ],
    }


def may_teach(staff, as_at: date | None = None) -> bool:
    return clearance_state(staff, as_at)["may_teach"]


def assert_may_teach(staff, as_at: date | None = None):
    """
    Raise unless this person may be assigned to students.

    Called from the serializers that set `ClassSection.teacher` and
    `TimetableSlot.teacher`, so an expired clearance blocks the assignment at
    the point it is made rather than being noticed at audit time.
    """
    state = clearance_state(staff, as_at)
    if state["may_teach"]:
        return
    problems = ", ".join(
        f"{StaffClearance(kind=b['kind']).get_kind_display()} ({b['reason']})"
        for b in state["blocking"]
    )
    raise ComplianceError(
        f"{state['name']} cannot be assigned to a class: {problems}. "
        f"Record and verify the credential before assigning teaching duties."
    )


def expiring_clearances(tenant_id, within_days: int = StaffClearance.EXPIRY_WARNING_DAYS,
                        as_at: date | None = None):
    """
    Credentials that have lapsed or are about to — the registrar's worklist.

    Expired first, then soonest-expiring: the order someone has to act in.
    Staff who have left are excluded; chasing a renewal from someone who
    resigned in March is noise that hides the real cases.
    """
    as_at = as_at or timezone.localdate()
    horizon = as_at + timedelta(days=within_days)
    qs = StaffClearance.objects.select_related("staff").filter(
        tenant_id=tenant_id, staff__is_active=True,
    ).filter(
        Q(expires_on__lte=horizon) | Q(verified_on__isnull=True)
    ).exclude(expires_on__isnull=True, verified_on__isnull=False)

    rows = []
    for clearance in qs:
        status = clearance.status(as_at)
        if status == StaffClearance.STATUS_VALID:
            continue
        rows.append({
            "clearance": str(clearance.id),
            "staff": str(clearance.staff_id),
            "name": f"{clearance.staff.first_name} {clearance.staff.last_name}".strip(),
            "kind": clearance.kind,
            "number": clearance.number,
            "expires_on": clearance.expires_on.isoformat() if clearance.expires_on else None,
            "days_until_expiry": clearance.days_until_expiry(as_at),
            "status": status,
            "blocks_teaching": clearance.kind in StaffClearance.BLOCKING_KINDS,
        })
    order = {
        StaffClearance.STATUS_EXPIRED: 0,
        StaffClearance.STATUS_UNVERIFIED: 1,
        StaffClearance.STATUS_EXPIRING: 2,
    }
    rows.sort(key=lambda r: (order.get(r["status"], 9), r["days_until_expiry"] if r["days_until_expiry"] is not None else 9999))
    return rows


def staff_blocked_from_teaching(tenant_id, as_at: date | None = None):
    """
    Active staff who currently hold a class but may not — the list a principal
    needs before Monday, because each row is a class that needs covering.
    """
    as_at = as_at or timezone.localdate()
    blocked = []
    for staff in Staff.objects.filter(tenant_id=tenant_id, is_active=True).prefetch_related(
        "clearances", "class_sections"
    ):
        state = clearance_state(staff, as_at)
        if state["may_teach"]:
            continue
        state["class_sections"] = list(
            staff.class_sections.values_list("name", flat=True)
        )
        blocked.append(state)
    return blocked


# ── leave entitlements ───────────────────────────────────────────────────────
def fte_for(staff, year: int) -> Decimal:
    """
    The FTE to pro-rate entitlements by.

    Prefers the contract current at the time; falls back to the most recent.
    A casual has no accrued leave entitlement under the NES, which is why the
    contract type matters and not just the fraction.
    """
    contract = (
        Contract.objects.filter(tenant_id=staff.tenant_id, staff=staff, is_current=True)
        .order_by("-start_date")
        .first()
        or Contract.objects.filter(tenant_id=staff.tenant_id, staff=staff)
        .order_by("-start_date")
        .first()
    )
    if contract is None:
        return Decimal("1")
    if contract.contract_type == "casual":
        # Casuals are paid a loading in lieu of paid leave.
        return Decimal("0")
    return Decimal(contract.fte or 1)


def ensure_entitlements(staff, year: int, *, opening_balances=None):
    """
    Create this year's annual and personal-leave entitlements if absent.

    Idempotent: safe to run at the start of every leave year, and safe to run
    twice. Existing rows are left alone — a registrar who hand-adjusted an
    entitlement must not have it overwritten by a scheduled job.
    """
    opening_balances = opening_balances or {}
    fte = fte_for(staff, year)
    created = []
    for leave_type, full_days in LeaveEntitlement.NES_DAYS.items():
        entitlement, was_created = LeaveEntitlement.objects.get_or_create(
            tenant_id=staff.tenant_id, staff=staff, leave_type=leave_type, year=year,
            defaults={
                "entitled_days": (full_days * fte).quantize(Decimal("0.01")),
                "opening_balance": Decimal(opening_balances.get(leave_type, 0)),
            },
        )
        if was_created:
            created.append(entitlement)
    return created


def entitlement_for(staff, leave_type: str, year: int):
    return LeaveEntitlement.objects.filter(
        tenant_id=staff.tenant_id, staff=staff, leave_type=leave_type, year=year
    ).first()


def leave_balances(staff, year: int | None = None, as_at: date | None = None) -> dict:
    """Every balance for this person — what a staff member sees on their profile."""
    as_at = as_at or timezone.localdate()
    year = year or as_at.year
    rows = []
    for entitlement in LeaveEntitlement.objects.filter(
        tenant_id=staff.tenant_id, staff=staff, year=year
    ):
        rows.append({
            "leave_type": entitlement.leave_type,
            "year": entitlement.year,
            "opening_balance": str(entitlement.opening_balance),
            "entitled_days": str(entitlement.entitled_days),
            "accrued_to_date": str(entitlement.accrued_days(as_at)),
            "taken": str(entitlement.taken_days()),
            "balance": str(entitlement.balance(as_at)),
        })
    return {
        "staff": str(staff.id),
        "name": f"{staff.first_name} {staff.last_name}".strip(),
        "year": year,
        "as_at": as_at.isoformat(),
        "balances": rows,
    }


def check_leave_balance(leave, as_at: date | None = None) -> dict:
    """
    Would approving this request over-draw the balance?

    Returns a verdict rather than raising, because leadership is allowed to
    approve anyway — with a recorded reason. Unpaid and parental leave are not
    drawn from a balance at all: refusing them on accrual grounds would deny
    leave the employee is entitled to.
    """
    if leave.leave_type not in leave.ACCRUED_TYPES:
        return {"applicable": False, "sufficient": True, "reason": "not drawn from an accrued balance"}

    as_at = as_at or timezone.localdate()
    year = leave.start_date.year if leave.start_date else as_at.year
    entitlement = entitlement_for(leave.staff, leave.leave_type, year)
    if entitlement is None:
        return {
            "applicable": True,
            "sufficient": False,
            "reason": (
                f"No {leave.get_leave_type_display()} entitlement exists for {year}. "
                f"Create one before approving, or the balance is unknowable."
            ),
            "available": None,
            "requested": str(leave.days),
        }

    # The request itself is not yet approved, so it is not in `taken_days`.
    available = entitlement.balance(as_at)
    requested = Decimal(leave.days or 0)
    return {
        "applicable": True,
        "sufficient": requested <= available,
        "available": str(available),
        "requested": str(requested),
        "shortfall": str(max(Decimal("0"), requested - available)),
        "reason": (
            "" if requested <= available
            else f"{requested} days requested but only {available} accrued as at {as_at}."
        ),
    }
