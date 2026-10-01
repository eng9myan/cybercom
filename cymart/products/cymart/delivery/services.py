"""Delivery foundations: is a point servable, who's the nearest free
driver, and what's the live status of an order. Plain haversine distance
— no external maps API needed to run or test; swapping in a real
routing/ETA provider later changes these functions' internals, not their
callers, same posture as the payments/agent provider abstractions.
"""

from __future__ import annotations

import math
import uuid
from decimal import Decimal

from django.db import transaction

from products.cymart.orders.models import MarketplaceOrder

from .models import (
    AssignmentStatus,
    DeliveryAssignment,
    DeliveryRun,
    DeliveryRunStatus,
    DeliveryZone,
    Driver,
    TrackingEvent,
)

EARTH_RADIUS_KM = 6371.0088


class NoDriverAvailableError(Exception):
    pass


class OrderAlreadyAssignedError(Exception):
    pass


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    lat1, lng1, lat2, lng2 = (float(v) for v in (lat1, lng1, lat2, lng2))
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(min(1, a)))


class ZoneService:
    def is_deliverable(self, lat, lng) -> DeliveryZone | None:
        """Returns the first active zone covering this point, or None if
        it's outside every servable area."""
        for zone in DeliveryZone.objects.filter(is_active=True):
            if haversine_km(zone.center_lat, zone.center_lng, lat, lng) <= float(zone.radius_km):
                return zone
        return None

    def route_deliverable(self, store_lat, store_lng, customer_lat, customer_lng) -> bool:
        """Both ends of the trip must fall in a servable zone — a store
        just outside the launch city can't be matched to a customer just
        inside it via a technicality."""
        return (
            self.is_deliverable(store_lat, store_lng) is not None
            and self.is_deliverable(customer_lat, customer_lng) is not None
        )


class DispatchService:
    def _busy_driver_ids(self):
        return DeliveryAssignment.objects.filter(
            status__in=[AssignmentStatus.ASSIGNED, AssignmentStatus.PICKED_UP]
        ).values_list("driver_id", flat=True)

    def _nearest_driver(self, lat, lng) -> Driver | None:
        candidates = Driver.objects.filter(
            is_active=True, is_online=True,
            current_lat__isnull=False, current_lng__isnull=False,
        ).exclude(id__in=self._busy_driver_ids())

        nearest, nearest_distance = None, None
        for driver in candidates:
            distance = haversine_km(lat, lng, driver.current_lat, driver.current_lng)
            if nearest_distance is None or distance < nearest_distance:
                nearest, nearest_distance = driver, distance
        return nearest

    def assign_nearest_driver(
        self, order: MarketplaceOrder, store_lat, store_lng
    ) -> DeliveryAssignment:
        run = self.assign_batch([(order, store_lat, store_lng)])
        return run.assignments.get(order=order)

    def assign_batch(self, legs: list[tuple[MarketplaceOrder, object, object]]) -> DeliveryRun:
        """Dispatch one driver to cover several orders in one trip — the
        multi-stop case: a customer's food order and grocery order,
        batched together instead of sending two separate couriers.
        ``legs``: [(order, pickup_lat, pickup_lng), ...], one per store
        the driver needs to visit; a single-leg list is the plain
        single-order case assign_nearest_driver delegates to."""
        if not legs:
            raise ValueError("assign_batch requires at least one (order, lat, lng) leg.")

        orders = [leg[0] for leg in legs]
        clash = DeliveryAssignment.objects.filter(
            order__in=orders, status__in=[AssignmentStatus.ASSIGNED, AssignmentStatus.PICKED_UP]
        ).first()
        if clash is not None:
            raise OrderAlreadyAssignedError(
                f"Order {clash.order_id} already has an active assignment."
            )

        first_order, first_lat, first_lng = legs[0]
        driver = self._nearest_driver(first_lat, first_lng)
        if driver is None:
            raise NoDriverAvailableError("No online driver is available near this pickup.")

        with transaction.atomic():
            run = DeliveryRun.objects.create(driver=driver, customer_id=first_order.customer_id)
            for i, (order, _lat, _lng) in enumerate(legs):
                assignment = DeliveryAssignment.objects.create(
                    order=order, driver=driver, run=run, stop_order=i
                )
                TrackingEvent.objects.create(assignment=assignment, status=AssignmentStatus.ASSIGNED)
        return run


_TERMINAL_STATUSES = (AssignmentStatus.DELIVERED, AssignmentStatus.CANCELLED)


class TrackingService:
    def record_event(
        self, assignment: DeliveryAssignment, status: str, note: str = ""
    ) -> TrackingEvent:
        from django.utils import timezone

        with transaction.atomic():
            event = TrackingEvent.objects.create(assignment=assignment, status=status, note=note)
            assignment.status = status
            if status == AssignmentStatus.PICKED_UP:
                assignment.picked_up_at = timezone.now()
            elif status == AssignmentStatus.DELIVERED:
                assignment.delivered_at = timezone.now()
            assignment.save()

            # A batched run's driver is free again only once every leg it
            # carries has reached a terminal state.
            if assignment.run_id and status in _TERMINAL_STATUSES:
                run = assignment.run
                if not run.assignments.exclude(status__in=_TERMINAL_STATUSES).exists():
                    run.status = DeliveryRunStatus.COMPLETED
                    run.completed_at = timezone.now()
                    run.save(update_fields=["status", "completed_at"])
        return event

    def status_for_order(self, order: MarketplaceOrder) -> dict | None:
        assignment = (
            DeliveryAssignment.objects.filter(order=order).order_by("-assigned_at").first()
        )
        if assignment is None:
            return None
        return {
            "assignment_id": assignment.id,
            "status": assignment.status,
            "driver_name": assignment.driver.name,
            "run_id": assignment.run_id,
            "timeline": [
                {"status": e.status, "note": e.note, "occurred_at": e.occurred_at}
                for e in assignment.events.all()
            ],
        }

    def status_for_run(self, run: DeliveryRun) -> dict:
        """The driver-side view of a batched trip — every order it's
        carrying and each one's own status, e.g. picked up the food but
        still en route to the grocery store."""
        return {
            "run_id": run.id,
            "driver_name": run.driver.name,
            "status": run.status,
            "stops": [
                {
                    "order_id": a.order_id,
                    "stop_order": a.stop_order,
                    "status": a.status,
                }
                for a in run.assignments.order_by("stop_order")
            ],
        }
