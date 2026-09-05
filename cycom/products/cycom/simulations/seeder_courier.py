"""Write a courier `SimResult` into the cycom logistics tables for a demo tenant."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db import transaction

from products.cycom.logistics.models import (
    Carrier, DeliveryEvent, DeliveryOrder, Package, PackageItem, Route, RouteStop,
)
from products.cycom.logistics.services import recompute_delivery_order

from .engine_courier import SimResult
from .models import SimulationRun
from .scenarios import courier as C

UTC = ZoneInfo("UTC")


def _d(x):
    return Decimal(str(round(float(x), 3)))


class CourierSeeder:
    def __init__(self, result: SimResult, *, slug: str, tenant_name: str,
                 run: SimulationRun, stdout=None):
        self.r = result
        self.slug = slug
        self.tenant_name = tenant_name
        self.run = run
        self.tag = run.tag if run is not None else "SIM:pending"
        self.counts = defaultdict(int)
        self._out = stdout
        self.tenant_id = None
        self.carrier = None

    def log(self, m):
        if self._out:
            self._out.write(m)

    def _tenant(self):
        from platform.tenant.models import Tenant, TenantStatus, TenantType
        t, _ = Tenant.objects.update_or_create(
            slug=self.slug,
            defaults={"name": self.tenant_name, "display_name": self.tenant_name,
                      "tenant_type": TenantType.DEDICATED, "status": TenantStatus.ACTIVE,
                      "country_code": C.COUNTRY, "timezone": C.TIMEZONE, "locale": "en",
                      "metadata": {"city": C.CITY, "demo": True, "simulation": "courier"}})
        self.tenant_id = t.id
        return t.id

    def ensure_tenant(self):
        return self.tenant_id or self._tenant()

    @transaction.atomic
    def wipe(self):
        from platform.tenant.models import Tenant
        t = Tenant.objects.filter(slug=self.slug).first()
        if not t:
            return
        tid = t.id
        for M in (RouteStop, Route, DeliveryEvent, PackageItem, Package, DeliveryOrder, Carrier):
            M.objects.filter(tenant_id=tid).delete()
        SimulationRun.objects.filter(tenant_id=tid).exclude(pk=self.run.pk).delete()
        self.log(f"  wiped prior logistics data for '{self.slug}'")

    def seed(self) -> dict:
        self.ensure_tenant()
        tid = self.tenant_id
        self.carrier, _ = Carrier.objects.get_or_create(
            tenant_id=tid, code="OWN-FLEET",
            defaults={"name": f"{C.COMPANY_NAME} Fleet", "mode": "courier", "is_own_fleet": True})

        parcel_do: dict[int, DeliveryOrder] = {}
        for p in self.r.parcels:
            do = DeliveryOrder.objects.create(
                tenant_id=tid, number=f"CD-{p.intake_utc:%Y%m%d}-{p.ref:05d}",
                customer_name=p.recipient, customer_reference=p.sender,
                destination_city=p.zone, destination_country=C.COUNTRY,
                status=self._do_status(p.status), service_level=p.service_level,
                promised_date=p.promised_date,
                dispatched_at=None, delivered_at=p.delivered_utc,
                failure_reason="" if p.status != "returned" else "max delivery attempts reached",
                attempts=p.attempts)
            DeliveryOrder.objects.filter(pk=do.pk).update(created_at=p.intake_utc)
            L, W, Hh = p.dims_cm
            tare = round(0.15 + 0.02 * p.weight_kg, 3)
            pkg = Package.objects.create(
                tenant_id=tid, delivery_order=do, package_no="1", packaging_type="carton",
                net_weight_kg=_d(p.weight_kg), tare_weight_kg=_d(tare),
                gross_weight_kg=_d(p.weight_kg + tare),
                length_cm=_d(L), width_cm=_d(W), height_cm=_d(Hh),
                contents_description=f"{p.size} parcel from {p.sender}")
            PackageItem.objects.create(
                tenant_id=tid, package=pkg, description=f"Consignment from {p.sender}",
                quantity=Decimal("1"), unit_net_weight_kg=_d(p.weight_kg))
            recompute_delivery_order(do)
            parcel_do[p.ref] = do
            self.counts["delivery_orders"] += 1

            DeliveryEvent.objects.create(tenant_id=tid, delivery_order=do, event_type="created",
                                         occurred_at=p.intake_utc, location="Amman Hub")
            if p.delivered_utc:
                DeliveryEvent.objects.create(
                    tenant_id=tid, delivery_order=do, event_type="out_for_delivery",
                    occurred_at=p.delivered_utc - timedelta(hours=2), location="Amman Hub")
                DeliveryEvent.objects.create(
                    tenant_id=tid, delivery_order=do, event_type="delivered",
                    occurred_at=p.delivered_utc, location=p.zone,
                    pod_name=p.recipient, pod_reference=f"POD-{do.number}")
            elif p.status == "returned":
                DeliveryEvent.objects.create(
                    tenant_id=tid, delivery_order=do, event_type="returned",
                    occurred_at=p.intake_utc + timedelta(days=3), location="Amman Hub",
                    notes="returned to sender after 3 failed attempts")

        for rd in self.r.routes:
            route = Route.objects.create(
                tenant_id=tid, date=rd.day, name=f"{rd.day:%a} run",
                driver_name=rd.driver, vehicle_label=C.VAN_LABEL, status="completed",
                planned_distance_km=_d(rd.planned_km), actual_distance_km=_d(rd.actual_km),
                planned_stops=rd.planned_stops, completed_stops=rd.completed_stops,
                failed_stops=rd.failed_stops, load_weight_kg=_d(rd.load_kg),
                vehicle_capacity_kg=_d(rd.capacity_kg), fuel_cost=_d(rd.fuel_cost),
                started_at=rd.started_utc, ended_at=rd.ended_utc)
            bulk = []
            for st in rd.stops:
                bulk.append(RouteStop(
                    tenant_id=tid, route=route, sequence=st.seq, stop_type="delivery",
                    delivery_order=parcel_do.get(st.parcel_ref),
                    address=st.zone, actual_arrival=st.arrival_utc,
                    dwell_minutes=_d(st.dwell_min), distance_from_prev_km=_d(st.dist_km),
                    status="completed" if st.status == "completed" else "failed"))
            RouteStop.objects.bulk_create(bulk)
            self.counts["routes"] += 1
            self.counts["route_stops"] += len(bulk)

        self.run.record_counts = dict(self.counts)
        self.log(f"  logistics: {self.counts['delivery_orders']} delivery orders, "
                 f"{self.counts['routes']} routes, {self.counts['route_stops']} stops")
        return dict(self.counts)

    @staticmethod
    def _do_status(s):
        return {"delivered": "delivered", "returned": "returned", "failed": "failed",
                "out_for_delivery": "out_for_delivery", "at_hub": "packed"}.get(s, "packed")
