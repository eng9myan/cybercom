"""
eMAR services — schedule generation and the "five rights" administration check.

Barcode conventions (what the bedside scanner sends):
  * patient wristband  → the patient's UUID (CyMed patient id)
  * medication package → the drug code on the order (RxNorm / local code)
Both are compared exactly; a mismatch is a hard stop, not a warning.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from products.cymed.hospital.nursing.models import MedicationAdministration

# Minutes either side of the scheduled time inside which a dose is "on time".
# Outside it the nurse must record why (late / early dose).
ON_TIME_WINDOW_MIN = 60

# Order statuses a dose may be given against: the pharmacist has verified it.
GIVABLE_ORDER_STATUSES = {"verified", "active"}

# Hours between doses for common frequency codes.
FREQUENCY_HOURS = {
    "QD": 24, "OD": 24, "DAILY": 24, "Q24H": 24,
    "BID": 12, "Q12H": 12,
    "TID": 8, "Q8H": 8,
    "QID": 6, "Q6H": 6,
    "Q4H": 4, "Q3H": 3, "Q2H": 2, "Q1H": 1, "HOURLY": 1,
}
# First dose times for the named daily schedules (hospital standard times).
STANDARD_TIMES = {
    "QD": ["09:00"], "OD": ["09:00"], "DAILY": ["09:00"],
    "BID": ["09:00", "21:00"],
    "TID": ["08:00", "14:00", "22:00"],
    "QID": ["06:00", "12:00", "18:00", "24:00"],
}


class MarError(ValueError):
    """A dose cannot be recorded as asked; the message says why."""


def _norm(value: str) -> str:
    return (value or "").strip().upper().replace(" ", "")


def dose_times(order, start: datetime, hours: int) -> list[datetime]:
    """Scheduled dose times for ``order`` in [start, start + hours)."""
    freq = _norm(order.frequency)
    if order.order_type in ("prn", "continuous") or freq.startswith("PRN"):
        return []
    end = start + timedelta(hours=hours)
    if order.order_type in ("one_time", "stat") or freq in ("ONCE", "STAT"):
        return [start]
    if freq in STANDARD_TIMES:
        times = []
        day = start.replace(hour=0, minute=0, second=0, microsecond=0)
        while day < end:
            for hhmm in STANDARD_TIMES[freq]:
                h, m = (int(x) for x in hhmm.split(":"))
                t = day + timedelta(hours=h, minutes=m)
                if start <= t < end:
                    times.append(t)
            day += timedelta(days=1)
        return times
    step = FREQUENCY_HOURS.get(freq)
    if step is None:
        raise MarError(f"Unrecognised frequency '{order.frequency}': schedule doses manually.")
    times, t = [], start
    while t < end:
        times.append(t)
        t += timedelta(hours=step)
    return times


def generate_schedule(order, *, start: datetime | None = None, hours: int = 24) -> list[MedicationAdministration]:
    """Create the scheduled eMAR rows for the next ``hours``. Idempotent:
    a slot that already has a row is left alone."""
    if order.status not in GIVABLE_ORDER_STATUSES:
        raise MarError("Only pharmacist-verified / active orders can be scheduled.")
    start = start or timezone.now().replace(minute=0, second=0, microsecond=0)
    created = []
    for t in dose_times(order, start, hours):
        if order.stop_date and t.date() > order.stop_date:
            continue
        try:
            with transaction.atomic():
                created.append(MedicationAdministration.objects.create(
                    tenant_id=order.tenant_id, medication_order=order,
                    patient_id=order.patient_id, admission_id=order.admission_id,
                    scheduled_at=t, dose_unit=order.dose_unit, route=order.route,
                ))
        except IntegrityError:
            continue  # slot already on the MAR
    return created


def _check_five_rights(order, *, patient_barcode, medication_barcode, dose, route,
                       scheduled_at, at, reason, nurse, witness):
    if order.status not in GIVABLE_ORDER_STATUSES:
        raise MarError("Order is not verified/active — do not administer.")
    if _norm(patient_barcode) != _norm(str(order.patient_id)):
        raise MarError("Wrong patient: wristband does not match the order.")
    if _norm(medication_barcode) != _norm(order.drug_code):
        raise MarError("Wrong medication: package does not match the order.")
    if route and _norm(route) != _norm(order.route):
        raise MarError(f"Wrong route: order is {order.route}.")
    if dose and _norm(dose) != _norm(order.dose) and not reason:
        raise MarError(f"Dose differs from the order ({order.dose} {order.dose_unit}): a reason is required.")
    if scheduled_at and abs((at - scheduled_at).total_seconds()) > ON_TIME_WINDOW_MIN * 60 and not reason:
        raise MarError("Outside the administration window: record why the dose is early/late.")
    if order.is_controlled:
        if not witness:
            raise MarError("Controlled drug: an independent witness is required.")
        if _norm(witness) == _norm(nurse):
            raise MarError("The witness must be a different person from the administering nurse.")


@transaction.atomic
def administer(dose_row: MedicationAdministration, *, nurse: str, patient_barcode: str,
               medication_barcode: str, dose: str = "", route: str = "", site: str = "",
               reason: str = "", witness: str = "", notes: str = "") -> MedicationAdministration:
    row = MedicationAdministration.objects.select_for_update().get(pk=dose_row.pk)
    if row.status != "scheduled":
        raise MarError(f"Dose already recorded as {row.status}.")
    order = row.medication_order
    now = timezone.now()
    _check_five_rights(order, patient_barcode=patient_barcode, medication_barcode=medication_barcode,
                       dose=dose, route=route, scheduled_at=row.scheduled_at, at=now,
                       reason=reason, nurse=nurse, witness=witness)
    row.status = "given"
    row.administered_at = now
    row.administered_by = nurse
    row.witnessed_by = witness
    row.dose_given = dose or order.dose
    row.dose_unit = order.dose_unit
    row.route = route or order.route
    row.site = site
    row.reason = reason
    row.notes = notes
    row.patient_barcode_verified = row.medication_barcode_verified = True
    row.save()
    return row


@transaction.atomic
def administer_prn(order, *, nurse: str, patient_barcode: str, medication_barcode: str, reason: str,
                   dose: str = "", route: str = "", site: str = "", witness: str = "",
                   notes: str = "") -> MedicationAdministration:
    """An as-needed (or STAT) dose given outside any schedule. The indication
    is mandatory — "PRN" without a reason is not an auditable record."""
    if not reason:
        raise MarError("PRN doses need the indication (reason).")
    now = timezone.now()
    _check_five_rights(order, patient_barcode=patient_barcode, medication_barcode=medication_barcode,
                       dose=dose, route=route, scheduled_at=None, at=now,
                       reason=reason, nurse=nurse, witness=witness)
    return MedicationAdministration.objects.create(
        tenant_id=order.tenant_id, medication_order=order, patient_id=order.patient_id,
        admission_id=order.admission_id, status="given", administered_at=now,
        administered_by=nurse, witnessed_by=witness, dose_given=dose or order.dose,
        dose_unit=order.dose_unit, route=route or order.route, site=site, reason=reason,
        notes=notes, patient_barcode_verified=True, medication_barcode_verified=True,
    )


def mark_not_given(dose_row: MedicationAdministration, *, nurse: str, status: str, reason: str):
    if status not in ("held", "refused", "missed"):
        raise MarError("status must be held, refused or missed.")
    if not reason:
        raise MarError("A reason is required.")
    if dose_row.status != "scheduled":
        raise MarError(f"Dose already recorded as {dose_row.status}.")
    dose_row.status = status
    dose_row.reason = reason
    dose_row.administered_by = nurse
    dose_row.administered_at = timezone.now()
    dose_row.save(update_fields=["status", "reason", "administered_by", "administered_at", "updated_at"])
    return dose_row
