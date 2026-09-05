"""Roll-up recomputation for logistics aggregates."""
from decimal import Decimal

from .models import DeliveryOrder, Shipment

Z3 = Decimal("0.001")
Z4 = Decimal("0.0001")


def recompute_delivery_order(do: DeliveryOrder, *, save: bool = True) -> DeliveryOrder:
    packages = list(do.packages.all().prefetch_related("items"))
    net = Decimal("0")
    gross = Decimal("0")
    vol = Decimal("0")
    qty = Decimal("0")
    for p in packages:
        net += Decimal(p.net_weight_kg)
        gross += Decimal(p.gross_weight_kg or (Decimal(p.net_weight_kg) + Decimal(p.tare_weight_kg)))
        vol += p.volume_m3
        for it in p.items.all():
            qty += Decimal(it.quantity)
    do.net_weight_kg = net.quantize(Z3)
    do.gross_weight_kg = gross.quantize(Z3)
    do.volume_m3 = vol.quantize(Z4)
    do.quantity = qty.quantize(Z3)
    do.package_count = len(packages)
    if save:
        do.save(update_fields=["net_weight_kg", "gross_weight_kg", "volume_m3",
                               "quantity", "package_count", "updated_at"])
    return do


def recompute_shipment(shipment: Shipment, *, save: bool = True) -> Shipment:
    orders = list(shipment.delivery_orders.all())
    shipment.total_net_weight_kg = sum((Decimal(o.net_weight_kg) for o in orders), Decimal("0")).quantize(Z3)
    shipment.total_gross_weight_kg = sum((Decimal(o.gross_weight_kg) for o in orders), Decimal("0")).quantize(Z3)
    shipment.total_volume_m3 = sum((Decimal(o.volume_m3) for o in orders), Decimal("0")).quantize(Z4)
    shipment.total_quantity = sum((Decimal(o.quantity) for o in orders), Decimal("0")).quantize(Z3)
    shipment.total_packages = sum(o.package_count for o in orders)
    if save:
        shipment.save(update_fields=["total_net_weight_kg", "total_gross_weight_kg",
                                     "total_volume_m3", "total_quantity", "total_packages",
                                     "updated_at"])
    return shipment
