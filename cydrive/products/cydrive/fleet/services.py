"""
Dispatch engine — CyberCom master spec section 12: "must be policy-driven.
Do not place complex dispatch rules directly in controllers." Kept as its
own service class, not view/controller logic.

Scope for this pass: eligibility filtering (availability, vehicle
capability, zone, compliance) + two selection policies (nearest, highest
rating). Batch dispatch, route optimization, and reassignment-on-failure
are real follow-up work, not built here.
"""

from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import DeliveryJob, DeliveryJobStatus, Driver, DriverStatus


class NoEligibleDriverError(Exception):
    pass


class InvalidJobTransitionError(Exception):
    pass


@dataclass
class DispatchCandidate:
    driver: Driver
    distance_km: float | None = None


VALID_JOB_TRANSITIONS: dict[str, set[str]] = {
    DeliveryJobStatus.PENDING: {DeliveryJobStatus.ASSIGNED, DeliveryJobStatus.CANCELLED},
    DeliveryJobStatus.ASSIGNED: {DeliveryJobStatus.ACCEPTED, DeliveryJobStatus.REJECTED},
    DeliveryJobStatus.ACCEPTED: {DeliveryJobStatus.PICKED_UP, DeliveryJobStatus.CANCELLED},
    DeliveryJobStatus.REJECTED: {DeliveryJobStatus.PENDING},  # re-dispatch
    DeliveryJobStatus.PICKED_UP: {DeliveryJobStatus.IN_TRANSIT},
    DeliveryJobStatus.IN_TRANSIT: {DeliveryJobStatus.DELIVERED, DeliveryJobStatus.FAILED},
    DeliveryJobStatus.DELIVERED: set(),
    DeliveryJobStatus.FAILED: {DeliveryJobStatus.RETURNED, DeliveryJobStatus.PENDING},
    DeliveryJobStatus.RETURNED: set(),
    DeliveryJobStatus.CANCELLED: set(),
}


def transition_job(job: DeliveryJob, to_status: str) -> DeliveryJob:
    allowed = VALID_JOB_TRANSITIONS.get(job.status, set())
    if to_status not in allowed:
        raise InvalidJobTransitionError(
            f"Cannot transition DeliveryJob from '{job.status}' to '{to_status}'. "
            f"Allowed: {sorted(allowed) or '(terminal state)'}"
        )
    job.status = to_status
    now = timezone.now()
    if to_status == DeliveryJobStatus.PICKED_UP:
        job.picked_up_at = now
    elif to_status == DeliveryJobStatus.DELIVERED:
        job.delivered_at = now
    job.save()
    return job


class DispatchEngine:
    def eligible_drivers(self, job: DeliveryJob) -> list[Driver]:
        candidates = Driver.objects.filter(
            company_id=job.company_id, status=DriverStatus.AVAILABLE
        ).select_related("current_vehicle")

        eligible = []
        for driver in candidates:
            vehicle = driver.current_vehicle
            if vehicle is None:
                continue
            if not vehicle.is_active or not vehicle.is_compliant:
                continue
            if job.requires_temperature_control and not vehicle.is_temperature_controlled:
                continue
            if job.dropoff_address.get("zone") and driver.zone and driver.zone != job.dropoff_address.get("zone"):
                continue
            eligible.append(driver)
        return eligible

    def assign_nearest(self, job: DeliveryJob, driver_distances: dict[str, float] | None = None) -> DeliveryJob:
        """driver_distances: optional {driver_id: distance_km} — real distance
        computation (routing API) isn't wired up yet, so callers without it
        get eligibility-filtered assignment without a distance tiebreaker."""
        eligible = self.eligible_drivers(job)
        if not eligible:
            raise NoEligibleDriverError(f"No eligible driver for job {job.id}.")

        if driver_distances:
            eligible.sort(key=lambda d: driver_distances.get(str(d.id), float("inf")))

        return self._assign(job, eligible[0])

    def assign_highest_rated(self, job: DeliveryJob) -> DeliveryJob:
        eligible = self.eligible_drivers(job)
        if not eligible:
            raise NoEligibleDriverError(f"No eligible driver for job {job.id}.")
        best = max(eligible, key=lambda d: d.rating)
        return self._assign(job, best)

    def _assign(self, job: DeliveryJob, driver: Driver) -> DeliveryJob:
        with transaction.atomic():
            job.driver = driver
            job.vehicle = driver.current_vehicle
            job.assigned_at = timezone.now()
            job = transition_job(job, DeliveryJobStatus.ASSIGNED)
            driver.status = DriverStatus.ON_JOB
            driver.save(update_fields=["status"])
        return job

    def release_driver(self, job: DeliveryJob) -> None:
        """Called on delivery/failure/cancellation — frees the driver back
        to available so they can be dispatched again."""
        if job.driver is not None:
            job.driver.status = DriverStatus.AVAILABLE
            job.driver.save(update_fields=["status"])
