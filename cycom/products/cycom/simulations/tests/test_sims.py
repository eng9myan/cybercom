import io
from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command

from products.cycom.simulations.engine_anabtawi import AnabtawiSimulator
from products.cycom.simulations.engine_courier import CourierSimulator
from products.cycom.simulations.kpis_anabtawi import AnabtawiKpis
from products.cycom.simulations.kpis_courier import CourierKpis
from products.cycom.simulations.models import SimulationRun

START = date(2026, 3, 2)


# ----------------------------------------------------------------- courier

class TestCourierEngine:
    def _run(self, **kw):
        kw.setdefault("seed", 11)
        kw.setdefault("start_date", START)
        kw.setdefault("days", 7)
        return CourierSimulator(**kw).run()

    def test_deterministic(self):
        a, b = self._run(), self._run()
        assert len(a.parcels) == len(b.parcels)
        assert [p.status for p in a.parcels] == [p.status for p in b.parcels]

    def test_delivery_and_timing_sane(self):
        r = self._run()
        delivered = [p for p in r.parcels if p.status == "delivered"]
        assert len(delivered) > len(r.parcels) * 0.5
        assert all(p.delivered_utc >= p.intake_utc for p in delivered)
        s = CourierKpis(r).summary()
        assert 40 <= s["parcels"]["on_time_rate"] <= 100
        assert s["operations"]["total_distance_km"] > 0

    def test_route_optimization_cuts_distance(self):
        base = CourierKpis(self._run(variant="baseline")).summary()
        opt = CourierKpis(self._run(variant="route_optimization")).summary()
        assert opt["operations"]["total_distance_km"] < base["operations"]["total_distance_km"]


@pytest.mark.django_db
class TestCourierSeeder:
    def test_writes_logistics_records(self):
        from platform.tenant.models import Tenant
        from products.cycom.logistics.models import (
            DeliveryEvent, DeliveryOrder, Package, Route, RouteStop)
        out = io.StringIO()
        call_command("seed_courier_sim", wipe=True, no_files=True, seed=3,
                     start_date=START.isoformat(), days=4, slug="cycom-courier-test", stdout=out)
        tid = Tenant.objects.get(slug="cycom-courier-test").id
        assert DeliveryOrder.objects.filter(tenant_id=tid).count() > 20
        assert Package.objects.filter(tenant_id=tid).count() == \
               DeliveryOrder.objects.filter(tenant_id=tid).count()
        assert Route.objects.filter(tenant_id=tid).count() >= 3
        assert RouteStop.objects.filter(tenant_id=tid).count() > 10
        assert DeliveryEvent.objects.filter(tenant_id=tid, event_type="delivered").exists()
        run = SimulationRun.objects.filter(scenario="courier:baseline").latest("created_at")
        assert run.status == "COMPLETED"
        assert run.summary["parcels"]["intake"] == DeliveryOrder.objects.filter(tenant_id=tid).count()

    def test_wipe_idempotent(self):
        from platform.tenant.models import Tenant
        from products.cycom.logistics.models import DeliveryOrder
        for _ in range(2):
            call_command("seed_courier_sim", wipe=True, no_files=True, seed=3,
                         start_date=START.isoformat(), days=3, slug="cycom-courier-test2",
                         stdout=io.StringIO())
        tid = Tenant.objects.get(slug="cycom-courier-test2").id
        # deterministic engine + wipe => stable count
        n1 = DeliveryOrder.objects.filter(tenant_id=tid).count()
        call_command("seed_courier_sim", wipe=True, no_files=True, seed=3,
                     start_date=START.isoformat(), days=3, slug="cycom-courier-test2",
                     stdout=io.StringIO())
        assert DeliveryOrder.objects.filter(tenant_id=tid).count() == n1


# --------------------------------------------------------------- anabtawi

class TestAnabtawiEngine:
    def _run(self, **kw):
        kw.setdefault("seed", 9)
        kw.setdefault("start_date", START)
        kw.setdefault("days", 7)
        return AnabtawiSimulator(**kw).run()

    def test_deterministic(self):
        a, b = self._run(), self._run()
        assert len(a.batches) == len(b.batches)
        assert len(a.shipments) == len(b.shipments)

    def test_baseline_flows_end_to_end(self):
        r = self._run()
        assert r.batches and r.retail and r.export_orders and r.shipments
        s = AnabtawiKpis(r).summary()
        assert s["manufacturing"]["yield_pct"] > 80
        assert s["export"]["total_net_weight_kg"] > 0
        assert s["export"]["total_gross_weight_kg"] > s["export"]["total_net_weight_kg"]
        assert s["financials"]["gross_margin"] > 0

    def test_raw_shortage_blocks_production(self):
        base = AnabtawiKpis(self._run(variant="baseline")).summary()
        short = AnabtawiKpis(self._run(variant="raw_shortage")).summary()
        assert short["manufacturing"]["blocked_batches"] > base["manufacturing"]["blocked_batches"]
        assert short["manufacturing"]["good_kg"] < base["manufacturing"]["good_kg"]


@pytest.mark.django_db
class TestAnabtawiSeeder:
    def test_writes_manufacturing_sales_logistics(self):
        from platform.tenant.models import Tenant
        from products.cycom.logistics.models import DeliveryOrder, Package, Shipment
        from products.cycom.manufacturing.models import BillOfMaterial, ManufacturingOrder
        from products.cycom.sales.models import SalesOrder
        out = io.StringIO()
        call_command("seed_anabtawi_sim", wipe=True, no_files=True, seed=4,
                     start_date=START.isoformat(), days=5, slug="cycom-anabtawi-test", stdout=out)
        tid = Tenant.objects.get(slug="cycom-anabtawi-test").id
        assert BillOfMaterial.objects.filter(tenant_id=tid).count() == 6
        assert ManufacturingOrder.objects.filter(tenant_id=tid).count() > 10
        assert SalesOrder.objects.filter(tenant_id=tid, customer_type="retail").count() > 5
        assert Shipment.objects.filter(tenant_id=tid).count() >= 1
        assert DeliveryOrder.objects.filter(tenant_id=tid).count() >= 1

        # carton weight rollup: a delivery order's gross == sum of package gross
        do = (DeliveryOrder.objects.filter(tenant_id=tid, package_count__gt=0)
              .prefetch_related("packages").first())
        pkg_gross = sum((p.gross_weight_kg for p in do.packages.all()), Decimal("0"))
        assert abs(do.gross_weight_kg - pkg_gross) < Decimal("0.01")
        assert do.gross_weight_kg > do.net_weight_kg

        run = SimulationRun.objects.filter(scenario="anabtawi:baseline").latest("created_at")
        assert run.status == "COMPLETED"
