"""
Test helpers for staff compliance.

A `Staff` row on its own can no longer be put in front of a class — a current
WWCC and teacher registration are required, and a missing credential blocks the
assignment exactly like an expired one. That is the point of the rule, but it
means any test that assigns a teacher has to build a compliant one.

Kept here rather than duplicated per test module so the definition of "cleared
to teach" lives in one place: when the blocking set changes, the fixtures
follow automatically.
"""

from datetime import timedelta

from django.utils import timezone

from products.cyed.hr.models import StaffClearance


def clear_for_teaching(staff, *, years_valid: int = 2, verified_by="registrar@cyed.edu.au"):
    """
    Give `staff` every credential required for classroom contact, valid and
    verified. Returns the created clearances.
    """
    today = timezone.localdate()
    created = []
    for kind in sorted(StaffClearance.BLOCKING_KINDS):
        clearance, _ = StaffClearance.objects.update_or_create(
            tenant_id=staff.tenant_id, staff=staff, kind=kind,
            defaults={
                "number": f"{kind.upper()}-{str(staff.id)[:8]}",
                "issued_on": today - timedelta(days=30),
                "expires_on": today + timedelta(days=365 * years_valid),
                "verified_on": today - timedelta(days=30),
                "verified_by": verified_by,
            },
        )
        created.append(clearance)
    return created
