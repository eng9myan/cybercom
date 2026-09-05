from datetime import date
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.hr.models import Employee
from apps.inventory.models import StockMovement
from apps.pos.models import PosOrder, PosOrderLine
from apps.purchasing.models import PurchaseOrder
from apps.simulations.engine import QsrSimulator
from apps.simulations.kpis import QsrKpis
from apps.simulations.models import SimulationRun
from apps.tenants.models import Branch, Company, Tenant

START = date(2026, 3, 2)   # a Monday


def _run(**kw):
    kw.setdefault("seed", 42)
    kw.setdefault("start_date", START)
    kw.setdefault("days", 2)
    kw.setdefault("volume", 0.05)
    kw.setdefault("countries", ["JO"])
    return QsrSimulator(**kw).run()


class EngineTests(TestCase):
    def test_deterministic(self):
        a, b = _run(), _run()
        self.assertEqual(len(a.orders), len(b.orders))
        self.assertAlmostEqual(sum(o.total for o in a.orders),
                               sum(o.total for o in b.orders), places=2)

    def test_produces_activity(self):
        r = _run()
        self.assertGreater(len(r.orders), 50)
        self.assertTrue(r.opening)
        self.assertTrue(all(o.served_utc >= o.placed_utc for o in r.orders))

    def test_full_week_triggers_replenishment(self):
        r = _run(days=7, volume=0.6)
        self.assertTrue(r.deliveries, "a full busy week should need supplier deliveries")
        self.assertTrue(any(d.status in ("RECEIVED", "PARTIAL") for d in r.deliveries))

    def test_never_oversells_stock(self):
        r = _run()
        opening = {}
        for op in r.opening:
            opening[(op.branch_code, op.sku)] = opening.get((op.branch_code, op.sku), 0.0) + op.qty
        received = {}
        for dv in r.deliveries:
            if dv.status in ("RECEIVED", "PARTIAL"):
                for sku, q in dv.lines.items():
                    received[(dv.branch_code, sku)] = received.get((dv.branch_code, sku), 0.0) + q
        used = {}
        for c in r.consumption:
            used[(c.branch_code, c.sku)] = used.get((c.branch_code, c.sku), 0.0) + c.usage_qty + c.waste_qty
        for key, u in used.items():
            available = opening.get(key, 0.0) + received.get(key, 0.0)
            self.assertLessEqual(u, available + 1e-6,
                                 f"{key}: consumed {u} > available {available}")

    def test_kitchen_waits_are_realistic(self):
        r = _run(volume=0.4)
        waits = [o.wait_seconds for o in r.orders]
        avg = sum(waits) / len(waits)
        self.assertLess(avg, 900, f"avg wait {avg:.0f}s is implausible for a QSR")
        self.assertTrue(all(w >= 0 for w in waits))

    def test_supply_disruption_bites(self):
        base = _run(variant="baseline", countries=["JO"], days=5, volume=0.3)
        dis = _run(variant="supply_disruption", countries=["JO"], days=5, volume=0.3)
        base_potato = sum(c.usage_qty for c in base.consumption
                          if c.branch_code == "JO-B2" and c.sku == "RM-POTATO")
        dis_potato = sum(c.usage_qty for c in dis.consumption
                         if c.branch_code == "JO-B2" and c.sku == "RM-POTATO")
        self.assertLess(dis_potato, base_potato,
                        "potato usage at JO-B2 should fall during the disruption")
        self.assertTrue(dis.disruption_log)


class KpiTests(TestCase):
    def test_summary_shape(self):
        s = QsrKpis(_run()).summary()
        for key in ("totals", "service", "inventory", "labor", "by_country",
                    "by_branch", "by_day", "csat_proxy"):
            self.assertIn(key, s)
        self.assertGreaterEqual(s["service"]["on_time_rate"], 0)
        self.assertLessEqual(s["service"]["on_time_rate"], 100)
        self.assertGreaterEqual(s["csat_proxy"], 0)
        self.assertEqual(s["totals"]["orders"], len(_run().orders))


class SeederTests(TestCase):
    def _seed(self, **extra):
        out = StringIO()
        call_command("seed_qsr_sim", wipe=True, no_files=True,
                     seed=7, start_date=START.isoformat(), days=6, volume=0.35,
                     countries="JO", subdomain="qsr-test", stdout=out)
        return out.getvalue()

    def test_seed_writes_business_records(self):
        self._seed()
        tenant = Tenant.objects.get(subdomain="qsr-test")
        tid = tenant.id
        self.assertEqual(Company.objects.filter(tenant_id=tid).count(), 4)
        self.assertEqual(Branch.objects.filter(tenant_id=tid).count(), 16)
        self.assertGreater(PosOrder.objects.filter(tenant_id=tid).count(), 50)
        self.assertGreater(PosOrderLine.objects.filter(tenant_id=tid).count(), 50)
        self.assertGreater(PurchaseOrder.objects.filter(tenant_id=tid).count(), 0)
        self.assertGreater(Employee.objects.filter(tenant=tenant).count(), 0)

        types = set(StockMovement.objects.filter(tenant_id=tid)
                    .values_list("movement_type", flat=True))
        self.assertIn("OPENING", types)
        self.assertIn("ISSUE", types)

        run = SimulationRun.objects.filter(scenario="qsr:baseline").latest("created_at")
        self.assertEqual(run.status, "COMPLETED")
        self.assertEqual(run.summary["totals"]["orders"],
                         PosOrder.objects.filter(tenant_id=tid).count())

    def test_pos_orders_have_timing_and_daypart(self):
        self._seed()
        o = PosOrder.objects.filter(tenant_id=Tenant.objects.get(subdomain="qsr-test").id).first()
        self.assertIsNotNone(o.placed_at)
        self.assertIsNotNone(o.served_at)
        self.assertGreaterEqual(o.served_at, o.placed_at)
        self.assertIn(o.daypart, dict(PosOrder.DAYPART))
        self.assertIn(o.source, dict(PosOrder.SOURCE))

    def test_wipe_makes_reruns_idempotent(self):
        self._seed()
        tid = Tenant.objects.get(subdomain="qsr-test").id
        first = PosOrder.objects.filter(tenant_id=tid).count()
        self._seed()
        self.assertEqual(PosOrder.objects.filter(tenant_id=tid).count(), first)
