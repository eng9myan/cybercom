import uuid
from decimal import Decimal

import pytest

from products.cymart.delivery.models import AssignmentStatus, DeliveryRunStatus, DeliveryZone, Driver
from products.cymart.delivery.services import (
    DispatchService,
    NoDriverAvailableError,
    OrderAlreadyAssignedError,
    TrackingService,
    ZoneService,
    haversine_km,
)
from products.cymart.orders.models import MarketplaceOrder

# Amman city center, roughly.
AMMAN_LAT, AMMAN_LNG = Decimal("31.9539"), Decimal("35.9106")


def _order(customer_id=None):
    return MarketplaceOrder.objects.create(
        idempotency_key=str(uuid.uuid4()), tenant_id=uuid.uuid4(), store_id=uuid.uuid4(),
        customer_id=customer_id or uuid.uuid4(), subtotal=Decimal("20.00"), total_amount=Decimal("20.00"),
    )


def _driver(lat=AMMAN_LAT, lng=AMMAN_LNG, is_online=True, is_active=True):
    return Driver.objects.create(
        name="Test Driver", phone="+9627xxxxxxxx",
        current_lat=lat, current_lng=lng, is_online=is_online, is_active=is_active,
    )


@pytest.mark.django_db
class TestHaversine:
    def test_same_point_is_zero_distance(self):
        assert haversine_km(31.95, 35.91, 31.95, 35.91) == pytest.approx(0, abs=1e-6)

    def test_known_distance_amman_to_zarqa_roughly_20km(self):
        # Amman ~31.9539,35.9106 ; Zarqa ~32.0728,36.0876 -> ~22km
        d = haversine_km(31.9539, 35.9106, 32.0728, 36.0876)
        assert 15 < d < 30


@pytest.mark.django_db
class TestZoneService:
    def test_point_inside_zone_is_deliverable(self):
        DeliveryZone.objects.create(
            name="Amman", city="Amman", center_lat=AMMAN_LAT, center_lng=AMMAN_LNG,
            radius_km=Decimal("15"),
        )
        zone = ZoneService().is_deliverable(AMMAN_LAT, AMMAN_LNG)
        assert zone is not None and zone.name == "Amman"

    def test_point_outside_every_zone_is_not_deliverable(self):
        DeliveryZone.objects.create(
            name="Amman", city="Amman", center_lat=AMMAN_LAT, center_lng=AMMAN_LNG,
            radius_km=Decimal("5"),
        )
        # ~150km away
        assert ZoneService().is_deliverable(Decimal("30.5"), Decimal("35.5")) is None

    def test_inactive_zone_is_ignored(self):
        DeliveryZone.objects.create(
            name="Amman", city="Amman", center_lat=AMMAN_LAT, center_lng=AMMAN_LNG,
            radius_km=Decimal("15"), is_active=False,
        )
        assert ZoneService().is_deliverable(AMMAN_LAT, AMMAN_LNG) is None

    def test_route_deliverable_requires_both_ends_in_zone(self):
        DeliveryZone.objects.create(
            name="Amman", city="Amman", center_lat=AMMAN_LAT, center_lng=AMMAN_LNG,
            radius_km=Decimal("15"),
        )
        svc = ZoneService()
        assert svc.route_deliverable(AMMAN_LAT, AMMAN_LNG, AMMAN_LAT, AMMAN_LNG) is True
        assert svc.route_deliverable(AMMAN_LAT, AMMAN_LNG, Decimal("30.5"), Decimal("35.5")) is False


@pytest.mark.django_db
class TestDispatchService:
    def test_assigns_nearest_online_driver(self):
        near = _driver(lat=AMMAN_LAT, lng=AMMAN_LNG)
        far = _driver(lat=Decimal("32.5"), lng=Decimal("36.5"))
        order = _order()
        assignment = DispatchService().assign_nearest_driver(order, AMMAN_LAT, AMMAN_LNG)
        assert assignment.driver_id == near.id
        assert assignment.driver_id != far.id
        assert assignment.status == AssignmentStatus.ASSIGNED

    def test_offline_driver_is_never_picked(self):
        _driver(is_online=False)
        with pytest.raises(NoDriverAvailableError):
            DispatchService().assign_nearest_driver(_order(), AMMAN_LAT, AMMAN_LNG)

    def test_busy_driver_is_skipped(self):
        driver = _driver()
        order1 = _order()
        DispatchService().assign_nearest_driver(order1, AMMAN_LAT, AMMAN_LNG)  # takes the only driver
        order2 = _order()
        with pytest.raises(NoDriverAvailableError):
            DispatchService().assign_nearest_driver(order2, AMMAN_LAT, AMMAN_LNG)

    def test_double_assignment_on_same_order_raises(self):
        _driver()
        _driver()
        order = _order()
        DispatchService().assign_nearest_driver(order, AMMAN_LAT, AMMAN_LNG)
        with pytest.raises(OrderAlreadyAssignedError):
            DispatchService().assign_nearest_driver(order, AMMAN_LAT, AMMAN_LNG)

    def test_creates_initial_assigned_tracking_event(self):
        _driver()
        order = _order()
        assignment = DispatchService().assign_nearest_driver(order, AMMAN_LAT, AMMAN_LNG)
        assert assignment.events.count() == 1
        assert assignment.events.first().status == AssignmentStatus.ASSIGNED


@pytest.mark.django_db
class TestTrackingService:
    def test_record_event_updates_assignment_status_and_timestamps(self):
        _driver()
        order = _order()
        assignment = DispatchService().assign_nearest_driver(order, AMMAN_LAT, AMMAN_LNG)
        TrackingService().record_event(assignment, AssignmentStatus.PICKED_UP)
        assignment.refresh_from_db()
        assert assignment.status == AssignmentStatus.PICKED_UP
        assert assignment.picked_up_at is not None

        TrackingService().record_event(assignment, AssignmentStatus.DELIVERED)
        assignment.refresh_from_db()
        assert assignment.status == AssignmentStatus.DELIVERED
        assert assignment.delivered_at is not None

    def test_status_for_order_returns_full_timeline(self):
        _driver()
        order = _order()
        assignment = DispatchService().assign_nearest_driver(order, AMMAN_LAT, AMMAN_LNG)
        TrackingService().record_event(assignment, AssignmentStatus.PICKED_UP, note="Left the store")
        status = TrackingService().status_for_order(order)
        assert status["status"] == AssignmentStatus.PICKED_UP
        assert len(status["timeline"]) == 2
        assert status["timeline"][1]["note"] == "Left the store"

    def test_status_for_unassigned_order_is_none(self):
        order = _order()
        assert TrackingService().status_for_order(order) is None


@pytest.mark.django_db
class TestBatchedDelivery:
    """The scenario the product is built on: a customer orders food from
    one merchant and groceries from another — one driver, one trip,
    two pickups — rather than two separate couriers."""

    def test_one_driver_covers_food_and_grocery_order(self):
        driver = _driver()
        customer_id = uuid.uuid4()
        food_order = _order(customer_id)
        grocery_order = _order(customer_id)

        run = DispatchService().assign_batch([
            (food_order, AMMAN_LAT, AMMAN_LNG),
            (grocery_order, Decimal("31.9642"), Decimal("35.8438")),  # a different merchant
        ])

        assert run.customer_id == customer_id
        assert run.driver_id == driver.id
        assert run.assignments.count() == 2
        stop_orders = sorted(run.assignments.values_list("stop_order", flat=True))
        assert stop_orders == [0, 1]
        # Both orders' own tracking still works independently.
        assert TrackingService().status_for_order(food_order)["run_id"] == run.id
        assert TrackingService().status_for_order(grocery_order)["run_id"] == run.id

    def test_batch_uses_only_one_driver_not_two(self):
        _driver()  # only one online driver available
        customer_id = uuid.uuid4()
        food_order, grocery_order = _order(customer_id), _order(customer_id)
        run = DispatchService().assign_batch([
            (food_order, AMMAN_LAT, AMMAN_LNG), (grocery_order, AMMAN_LAT, AMMAN_LNG),
        ])
        drivers_used = {a.driver_id for a in run.assignments.all()}
        assert len(drivers_used) == 1

    def test_batch_fails_if_any_order_already_assigned(self):
        _driver()
        customer_id = uuid.uuid4()
        food_order, grocery_order = _order(customer_id), _order(customer_id)
        DispatchService().assign_nearest_driver(food_order, AMMAN_LAT, AMMAN_LNG)
        with pytest.raises(OrderAlreadyAssignedError):
            DispatchService().assign_batch([
                (food_order, AMMAN_LAT, AMMAN_LNG), (grocery_order, AMMAN_LAT, AMMAN_LNG),
            ])

    def test_run_completes_only_after_every_leg_delivered(self):
        _driver()
        customer_id = uuid.uuid4()
        food_order, grocery_order = _order(customer_id), _order(customer_id)
        run = DispatchService().assign_batch([
            (food_order, AMMAN_LAT, AMMAN_LNG), (grocery_order, AMMAN_LAT, AMMAN_LNG),
        ])
        food_leg = run.assignments.get(order=food_order)
        grocery_leg = run.assignments.get(order=grocery_order)

        TrackingService().record_event(food_leg, AssignmentStatus.DELIVERED)
        run.refresh_from_db()
        assert run.status == DeliveryRunStatus.ACTIVE  # grocery leg still outstanding

        TrackingService().record_event(grocery_leg, AssignmentStatus.DELIVERED)
        run.refresh_from_db()
        assert run.status == DeliveryRunStatus.COMPLETED
        assert run.completed_at is not None

    def test_run_status_reports_every_stop(self):
        _driver()
        customer_id = uuid.uuid4()
        food_order, grocery_order = _order(customer_id), _order(customer_id)
        run = DispatchService().assign_batch([
            (food_order, AMMAN_LAT, AMMAN_LNG), (grocery_order, AMMAN_LAT, AMMAN_LNG),
        ])
        status = TrackingService().status_for_run(run)
        assert len(status["stops"]) == 2
        assert {s["order_id"] for s in status["stops"]} == {food_order.id, grocery_order.id}

    def test_single_order_dispatch_still_works_unbatched(self):
        # assign_nearest_driver now delegates to assign_batch internally
        # — this locks in that its return shape is unchanged.
        _driver()
        order = _order()
        assignment = DispatchService().assign_nearest_driver(order, AMMAN_LAT, AMMAN_LNG)
        assert assignment.order_id == order.id
        assert assignment.status == AssignmentStatus.ASSIGNED
        assert assignment.run is not None
        assert assignment.run.assignments.count() == 1
