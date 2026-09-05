"""
Seed a diversified sweets business (manufacturing + retail + export) into a
cycom demo tenant.

    python manage.py seed_anabtawi_sim --wipe
    python manage.py seed_anabtawi_sim --scenario peak_export --wipe
    python manage.py seed_anabtawi_sim --scenario raw_shortage --wipe
    python manage.py seed_anabtawi_sim --scenario plant_downtime --wipe
    python manage.py seed_anabtawi_sim --scenario retail_promo --wipe

"Anabtawi Group" — a plant producing oriental sweets in batches, a 4-branch
retail network, and consolidated international shipments to SA / AE / US / DE.
Writes manufacturing orders, retail sales orders and logistics shipments /
delivery orders / cartons into the cycom tables, then rolls up production yield,
QC, retail revenue, export on-time %, freight and gross margin.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from products.cycom.simulations.engine_anabtawi import AnabtawiSimulator
from products.cycom.simulations.kpis_anabtawi import AnabtawiKpis
from products.cycom.simulations.models import SimulationRun
from products.cycom.simulations.scenarios import anabtawi as A
from products.cycom.simulations.seeder_anabtawi import AnabtawiSeeder


class Command(BaseCommand):
    help = "Seed the Anabtawi multi-line sweets business into a cycom demo tenant."

    def add_arguments(self, parser):
        parser.add_argument("--scenario", default="baseline", choices=sorted(A.VARIANTS))
        parser.add_argument("--seed", type=int, default=20260905)
        parser.add_argument("--start-date", default=None)
        parser.add_argument("--days", type=int, default=7)
        parser.add_argument("--scale", type=float, default=1.0)
        parser.add_argument("--slug", default="cycom-anabtawi-sim")
        parser.add_argument("--tenant-name", default="Anabtawi Group (Demo)")
        parser.add_argument("--wipe", action="store_true")
        parser.add_argument("--out", default=None)
        parser.add_argument("--no-files", action="store_true")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        if opts["start_date"]:
            try:
                start = datetime.strptime(opts["start_date"], "%Y-%m-%d").date()
            except ValueError:
                raise CommandError("--start-date must be YYYY-MM-DD")
        else:
            start = timezone.now().date() - timedelta(days=opts["days"])

        scn = opts["scenario"]
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Anabtawi simulation - {scn}: {A.VARIANTS[scn]['label']}"))
        sim = AnabtawiSimulator(seed=opts["seed"], start_date=start, days=opts["days"],
                                variant=scn, scale=opts["scale"])
        result = sim.run()
        self.stdout.write(f"  engine : {len(result.batches)} batches, "
                          f"{len(result.retail)} retail lines, {len(result.export_orders)} export orders, "
                          f"{len(result.shipments)} shipments")

        kpis = AnabtawiKpis(result)
        out_dir = Path(opts["out"]) if opts["out"] else (
            Path(settings.BASE_DIR).parent / "simulation_output" / f"anabtawi-{scn}-{start:%Y%m%d}")

        run = None
        if not opts["dry_run"]:
            seeder = AnabtawiSeeder(result, slug=opts["slug"], tenant_name=opts["tenant_name"],
                                    run=None, stdout=self.stdout)
            tid = seeder.ensure_tenant()
            run = SimulationRun.objects.create(
                tenant_id=tid, scenario=f"anabtawi:{scn}", seed=opts["seed"], start_date=start,
                days=opts["days"], status="RUNNING",
                parameters={"variant": scn, "scale": opts["scale"], "slug": opts["slug"]})
            seeder.run = run
            seeder.tag = run.tag
            try:
                if opts["wipe"]:
                    seeder.wipe()
                seeder.seed()
            except Exception as exc:   # noqa: BLE001
                run.status = "FAILED"
                run.error = repr(exc)
                run.save(update_fields=["status", "error"])
                raise
            run.summary = kpis.summary()
            run.status = "COMPLETED"
            run.completed_at = timezone.now()
            run.save()

        s = run.summary if run else kpis.summary()
        files = [] if opts["no_files"] else kpis.write_files(out_dir)

        m, rw, rt, ex, fi = (s["manufacturing"], s["raw_materials"], s["retail"],
                             s["export"], s["financials"])
        w = self.stdout.write
        w("")
        w(self.style.SUCCESS("=== KPI summary ==="))
        w(f"  manufacturing  : {m['batches']} batches ({m['blocked_batches']} blocked)   "
          f"{m['good_kg']:,.0f} kg good   yield {m['yield_pct']}%   QC defect {m['qc_defect_pct']}%")
        w(f"  raw materials  : {rw['receipts']} receipts   {rw['received_value']:,.0f} value   "
          f"{rw['shortage_blocked_batches']} batches blocked by shortage")
        w(f"  retail         : {rt['revenue']:,.0f} rev   {rt['kg_sold']:,.0f} kg   "
          f"{rt['sales_orders']} branch-day orders")
        w(f"  export         : {ex['orders']} orders -> {ex['shipments']} shipments "
          f"(consolidation {ex['consolidation_ratio']}x)   on-time {ex['on_time_pct']}%")
        w(f"  export weight  : net {ex['total_net_weight_kg']:,.0f} kg   "
          f"gross {ex['total_gross_weight_kg']:,.0f} kg   {ex['total_cartons']:,} cartons   "
          f"backorder {ex['backorder_kg']} kg")
        w(f"  freight        : {ex['freight_cost']:,.0f}   {ex['freight_per_kg']}/kg")
        w(f"  financials     : revenue {fi['total_revenue']:,.0f}   "
          f"gross margin {fi['gross_margin']:,.0f} ({fi['gross_margin_pct']}%)")
        w("")
        w("  export by destination:")
        for d in ex["by_destination"]:
            w(f"    {d['country']}: {d['orders']} ord  {d['shipments']} shp  "
              f"{d['net_kg']:,.0f} kg  {d['cartons']} ctn  {d['on_time_pct']}% OT  "
              f"freight {d['freight']:,.0f}")
        if s["disruptions"]:
            for d in s["disruptions"]:
                w(f"  disruption: {d}")
        if run:
            w(f"  SimulationRun  : {run.pk}  " +
              ", ".join(f"{k}={v}" for k, v in sorted(run.record_counts.items())))
        for f in files:
            w(f"    {f}")
