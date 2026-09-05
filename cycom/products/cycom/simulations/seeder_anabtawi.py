"""Write an Anabtawi `SimResult` into cycom tables (manufacturing / sales / logistics)."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db import transaction

from products.cycom.accounting.models import Account
from products.cycom.inventory.models import Product, Warehouse
from products.cycom.logistics.models import (
    Carrier, DeliveryEvent, DeliveryOrder, Package, PackageItem, Shipment,
)
from products.cycom.logistics.services import recompute_delivery_order, recompute_shipment
from products.cycom.manufacturing.models import BillOfMaterial, BOMComponent, ManufacturingOrder
from products.cycom.sales.models import SalesOrder, SalesOrderLine

from .engine_anabtawi import SimResult
from .models import SimulationRun
from .scenarios import anabtawi as A

UTC = ZoneInfo("UTC")


def _d(x):
    return Decimal(str(round(float(x), 4)))


class AnabtawiSeeder:
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
        self.products: dict[str, Product] = {}
        self.boms: dict[str, BillOfMaterial] = {}
        self.wh_plant = None
        self.wh_export = None
        self.wip = None

    def log(self, m):
        if self._out:
            self._out.write(m)

    def _tenant(self):
        from platform.tenant.models import Tenant, TenantStatus, TenantType
        t, _ = Tenant.objects.update_or_create(
            slug=self.slug,
            defaults={"name": self.tenant_name, "display_name": self.tenant_name,
                      "tenant_type": TenantType.DEDICATED, "status": TenantStatus.ACTIVE,
                      "country_code": A.ORIGIN_COUNTRY, "timezone": A.TIMEZONE, "locale": "en",
                      "metadata": {"city": A.ORIGIN_CITY, "demo": True, "simulation": "anabtawi",
                                   "divisions": list(A.DIVISIONS)}})
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
        for M in (DeliveryEvent, PackageItem, Package, DeliveryOrder, Shipment, Carrier,
                  SalesOrderLine, SalesOrder, ManufacturingOrder, BOMComponent, BillOfMaterial):
            M.objects.filter(tenant_id=tid).delete()
        Product.objects.filter(tenant_id=tid).delete()
        SimulationRun.objects.filter(tenant_id=tid).exclude(pk=self.run.pk).delete()
        self.log(f"  wiped prior Anabtawi data for '{self.slug}'")

    def seed(self) -> dict:
        tid = self.ensure_tenant()
        inv_acc, _ = Account.objects.get_or_create(
            tenant_id=tid, code="1400", defaults={"name": "Inventory", "account_type": "asset"})
        self.wip, _ = Account.objects.get_or_create(
            tenant_id=tid, code="1500", defaults={"name": "Work in Progress", "account_type": "asset"})
        self.wh_plant, _ = Warehouse.objects.get_or_create(
            tenant_id=tid, code="WH-PLANT", defaults={"name": "Manufacturing Plant Store"})
        self.wh_export, _ = Warehouse.objects.get_or_create(
            tenant_id=tid, code="WH-EXPORT", defaults={"name": "Export Consolidation Warehouse"})

        for rm in A.RAW_MATERIALS:
            p, _ = Product.objects.get_or_create(
                tenant_id=tid, sku=rm.sku,
                defaults={"name": rm.name, "uom": "kg", "inventory_account": inv_acc})
            self.products[rm.sku] = p
        for fg in A.PRODUCTS:
            p, _ = Product.objects.get_or_create(
                tenant_id=tid, sku=fg.sku,
                defaults={"name": fg.name, "uom": "kg", "inventory_account": inv_acc})
            self.products[fg.sku] = p
            bom, created = BillOfMaterial.objects.get_or_create(
                tenant_id=tid, product=p, name=f"{fg.name} — standard recipe",
                defaults={"quantity": _d(fg.batch_kg)})
            self.boms[fg.sku] = bom
            if created:
                for sku, per in fg.recipe.items():
                    BOMComponent.objects.get_or_create(
                        tenant_id=tid, bom=bom, component=self.products[sku],
                        defaults={"quantity": _d((fg.batch_kg / fg.yield_pct) * per)})
        self.counts["products"] = Product.objects.filter(tenant_id=tid).count()

        self._seed_production(tid)
        self._seed_retail(tid)
        self._seed_export(tid)

        self.run.record_counts = dict(self.counts)
        return dict(self.counts)

    def _seed_production(self, tid):
        for b in self.r.batches:
            mo = ManufacturingOrder.objects.create(
                tenant_id=tid, bom=self.boms[b.product_sku],
                quantity=_d(b.good_kg if not b.blocked else 0),
                warehouse=self.wh_plant, wip_account=self.wip,
                status="cancelled" if b.blocked else "done",
                scheduled_date=b.day,
                reference=f"{self.tag} {'BLOCKED ' if b.blocked else ''}{b.note}".strip())
            ManufacturingOrder.objects.filter(pk=mo.pk).update(
                created_at=datetime.combine(b.day, time(7, 0), tzinfo=UTC))
            self.counts["manufacturing_orders"] += 1
            if b.blocked:
                self.counts["blocked_batches"] += 1
        self.log(f"  manufacturing: {self.counts['manufacturing_orders']} orders "
                 f"({self.counts['blocked_batches']} blocked)")

    def _seed_retail(self, tid):
        by_bd = defaultdict(list)
        for s in self.r.retail:
            by_bd[(s.branch, s.day)].append(s)
        n = 0
        for (branch, day), sales in sorted(by_bd.items()):
            so = SalesOrder.objects.create(
                tenant_id=tid, number=f"RET-{branch}-{day:%Y%m%d}",
                customer_name=f"Retail counter — {branch}", customer_type="retail",
                order_date=day, currency=A.CURRENCY, status="delivered",
                salesperson=branch, notes=f"{self.tag} retail day")
            SalesOrder.objects.filter(pk=so.pk).update(
                created_at=datetime.combine(day, time(20, 0), tzinfo=UTC))
            for s in sales:
                fg = A.PRODUCT_BY_SKU[s.product_sku]
                SalesOrderLine.objects.create(
                    tenant_id=tid, order=so, product=self.products[s.product_sku],
                    description=fg.name, quantity=_d(s.kg),
                    unit_price=_d(fg.retail_per_kg), tax_percent=Decimal("16"))
            so.recompute_totals()
            n += 1
        self.counts["retail_sales_orders"] = n
        self.log(f"  retail: {n} branch-day sales orders")

    def _seed_export(self, tid):
        carriers = {}
        for dest in A.DESTINATIONS:
            c, _ = Carrier.objects.get_or_create(
                tenant_id=tid, code=f"CARR-{dest.mode.upper()}",
                defaults={"name": f"{dest.mode.title()} freight partner", "mode": dest.mode})
            carriers[dest.mode] = c

        order_do: dict[int, DeliveryOrder] = {}
        for idx, o in enumerate(self.r.export_orders):
            do = DeliveryOrder.objects.create(
                tenant_id=tid, number=f"EXP-DO-{o.order_day:%Y%m%d}-{idx:04d}",
                customer_name=o.distributor, destination_city=o.dest_city,
                destination_country=o.dest_country,
                status="delivered" if o.shipment_ref else ("packed" if o.fulfilled else "allocated"),
                service_level="standard", promised_date=o.promised_date)
            DeliveryOrder.objects.filter(pk=do.pk).update(
                created_at=datetime.combine(o.order_day, time(10, 0), tzinfo=UTC))
            for li, l in enumerate(o.lines):
                fg = A.PRODUCT_BY_SKU[l.product_sku]
                pkg = Package.objects.create(
                    tenant_id=tid, delivery_order=do, package_no=f"{li + 1}",
                    packaging_type="carton",
                    net_weight_kg=_d(l.net_kg), tare_weight_kg=_d(l.gross_kg - l.net_kg),
                    gross_weight_kg=_d(l.gross_kg),
                    length_cm=_d(A.CARTON_DIMS_CM[0]), width_cm=_d(A.CARTON_DIMS_CM[1]),
                    height_cm=_d(A.CARTON_DIMS_CM[2]),
                    contents_description=f"{fg.name} x{l.cartons} cartons")
                PackageItem.objects.create(
                    tenant_id=tid, package=pkg, sku=fg.sku, description=fg.name,
                    quantity=_d(l.net_kg), unit_net_weight_kg=Decimal("1"))
            recompute_delivery_order(do)
            order_do[idx] = do
            self.counts["export_delivery_orders"] += 1
            DeliveryEvent.objects.create(tenant_id=tid, delivery_order=do, event_type="created",
                                         occurred_at=DeliveryOrder.objects.get(pk=do.pk).created_at,
                                         location=f"{A.ORIGIN_CITY} plant")

        for sh in self.r.shipments:
            dest = next(d for d in A.DESTINATIONS if d.country == sh.dest_country)
            shipment = Shipment.objects.create(
                tenant_id=tid, number=f"EXP-SHP-{sh.ref:04d}", carrier=carriers[sh.mode],
                mode=sh.mode, incoterm=sh.incoterm, status="delivered",
                origin_name=f"{A.ORIGIN_CITY}, Jordan", origin_country=A.ORIGIN_COUNTRY,
                destination_name=f"{sh.dest_city}, {sh.dest_country}",
                destination_country=sh.dest_country,
                planned_pickup=sh.dispatch_utc, actual_pickup=sh.dispatch_utc,
                planned_delivery=datetime.combine(sh.promised_latest, time(12, 0), tzinfo=UTC),
                actual_delivery=sh.delivered_utc,
                freight_cost=_d(sh.freight_cost), currency=A.CURRENCY,
                notes=f"{self.tag} consolidated export")
            Shipment.objects.filter(pk=shipment.pk).update(created_at=sh.dispatch_utc)
            for oref in sh.order_refs:
                do = order_do.get(oref)
                if not do:
                    continue
                do.shipment = shipment
                do.dispatched_at = sh.dispatch_utc
                do.delivered_at = sh.delivered_utc
                do.status = "delivered"
                do.save(update_fields=["shipment", "dispatched_at", "delivered_at", "status",
                                       "updated_at"])
                for ev, when, loc in [
                    ("departed_hub", sh.dispatch_utc, f"{A.ORIGIN_CITY} plant"),
                    ("customs_hold", sh.arrival_utc, f"{sh.dest_city} port of entry"),
                    ("customs_cleared", sh.arrival_utc + timedelta(hours=sh.customs_hours),
                     f"{sh.dest_city} port of entry"),
                    ("delivered", sh.delivered_utc, sh.dest_city),
                ]:
                    DeliveryEvent.objects.create(tenant_id=tid, delivery_order=do, event_type=ev,
                                                 occurred_at=when, location=loc,
                                                 pod_name=do.customer_name if ev == "delivered" else "")
            recompute_shipment(shipment)
            self.counts["export_shipments"] += 1
        self.log(f"  export: {self.counts['export_shipments']} shipments, "
                 f"{self.counts['export_delivery_orders']} delivery orders")
