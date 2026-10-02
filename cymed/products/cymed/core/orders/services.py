"""Order-set application: one clinician action → ordinary Order rows."""
from collections import defaultdict

from django.db import transaction

from platform.canonical import events as canonical_events
from products.cymed.core.encounters.models import Encounter
from products.cymed.core.orders.models import Order, OrderItem, OrderPriority, OrderStatus
from products.cymed.core.patients.models import Patient

_PRIORITY_RANK = {OrderPriority.ROUTINE: 0, OrderPriority.URGENT: 1, OrderPriority.STAT: 2}


class OrderSetError(ValueError):
    pass


@transaction.atomic
def apply_order_set(order_set, *, tenant_id, patient_id, ordered_by, encounter_id=None, item_ids=None):
    """Create one active Order per order type from ``order_set``.

    ``item_ids`` narrows to the items the clinician kept ticked; without it
    every ``default_selected`` item is ordered. The patient (and encounter)
    must belong to ``tenant_id`` — ids arrive in the request body, so nothing
    upstream has checked them. Each Order takes the most urgent priority among
    its items."""
    patient = Patient.objects.filter(id=patient_id, tenant_id=tenant_id).first()
    if patient is None:
        raise OrderSetError("Patient not found.")
    encounter = None
    if encounter_id:
        encounter = Encounter.objects.filter(id=encounter_id, tenant_id=tenant_id, patient=patient).first()
        if encounter is None:
            raise OrderSetError("Encounter not found for this patient.")

    items = list(order_set.items.all())
    if item_ids is not None:
        wanted = {str(i) for i in item_ids}
        items = [i for i in items if str(i.id) in wanted]
        if len(items) != len(wanted):
            raise OrderSetError("Some item_ids are not part of this order set.")
    else:
        items = [i for i in items if i.default_selected]
    if not items:
        raise OrderSetError("Nothing to order: no items selected.")

    by_type = defaultdict(list)
    for item in items:
        by_type[item.order_type].append(item)

    orders = []
    for order_type, group in by_type.items():
        priority = max((i.priority for i in group), key=lambda p: _PRIORITY_RANK.get(p, 0))
        order = Order.objects.create(
            tenant_id=tenant_id, patient=patient, encounter=encounter,
            order_type=order_type, priority=priority, status=OrderStatus.ACTIVE,
            ordered_by=ordered_by,
        )
        for item in group:
            OrderItem.objects.create(
                tenant_id=tenant_id, order=order, code=item.code,
                display=item.display, quantity=item.quantity,
            )
        canonical_events.emit(
            event_type="cymed.order.created",
            aggregate_type="Order",
            aggregate_id=order.id,
            tenant_id=tenant_id,
            payload={"order_id": str(order.id), "patient_id": str(patient.id),
                     "type": order.order_type, "order_set": order_set.code},
        )
        orders.append(order)
    return orders
