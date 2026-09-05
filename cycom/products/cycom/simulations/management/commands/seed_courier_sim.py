"""
Seed a two-person last-mile courier operating week into a cycom demo tenant.

    python manage.py seed_courier_sim --wipe
    python manage.py seed_courier_sim --scenario surge --wipe
    python manage.py seed_courier_sim --scenario van_breakdown --wipe
    python manage.py seed_courier_sim --scenario route_optimization --wipe

One hub, one van, two employees. Generates parcel intake -> sort -> route ->
deliver -> POD / exception -> returns into the cycom logistics tables, and rolls
up the operations KPIs (on-time %, transit time, km per parcel, load + driver
utilisation, first-attempt success, cost per parcel).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from products.cycom.simulations.engine_courier import CourierSimulator
from products.cycom.simulations.kpis_courier import CourierKpis
from products.cycom.simulations.models import SimulationRun
from products.cycom.simulations.scenarios import courier as C
from products.cycom.simulations.seeder_courier import CourierSeeder


class Command(BaseCommand):
    help = "Seed a last-mile courier operating week into a cycom demo tenant."

    def add_arguments(self, parser):
        parser.add_argument("--scenario", default="baseline", choices=sorted(C.VARIANTS))
        parser.add_argument("--seed", type=int, default=20260905)
        parser.add_argument("--start-date", default=None)
        parser.add_argument("--days", type=int, default=7)
        parser.add_argument("--slug", default="cycom-courier-sim")
        parser.add_argument("--tenant-name", default="Cycom Courier Co (Demo)")
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
            f"Courier simulation - {scn}: {C.VARIANTS[scn]['label']}"))
        sim = CourierSimulator(seed=opts["seed"], start_date=start, days=opts["days"], variant=scn)
        result = sim.run()
        self.stdout.write(f"  engine : {len(result.parcels)} parcels, {len(result.routes)} routes")

        kpis = CourierKpis(result)
        out_dir = Path(opts["out"]) if opts["out"] else (
            Path(settings.BASE_DIR).parent / "simulation_output" / f"courier-{scn}-{start:%Y%m%d}")

        run = None
        if not opts["dry_run"]:
            seeder = CourierSeeder(result, slug=opts["slug"], tenant_name=opts["tenant_name"],
                                   run=None, stdout=self.stdout)
            tid = seeder.ensure_tenant()
            run = SimulationRun.objects.create(
                tenant_id=tid, scenario=f"courier:{scn}", seed=opts["seed"], start_date=start,
                days=opts["days"], status="RUNNING",
                parameters={"variant": scn, "slug": opts["slug"]})
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

        pk, op, co = s["parcels"], s["operations"], s["cost"]
        w = self.stdout.write
        w("")
        w(self.style.SUCCESS("=== KPI summary ==="))
        w(f"  parcels        : {pk['intake']} in   {pk['delivered']} delivered   "
          f"{pk['returned']} returned   {pk['undelivered_at_horizon']} still at hub")
        w(f"  service        : {pk['on_time_rate']}% on time   "
          f"first-attempt {pk['first_attempt_success_rate']}%   "
          f"transit avg {pk['avg_transit_hours']}h (p90 {pk['p90_transit_hours']}h)")
        w(f"  operations     : {op['routes']} routes   {op['total_distance_km']} km   "
          f"{op['km_per_delivered_parcel']} km/parcel   {op['avg_stops_per_route']} stops/route")
        w(f"  utilisation    : load {op['avg_load_factor_pct']}%   "
          f"driver {op['avg_driver_utilisation_pct']}%")
        w(f"  cost           : {co['total']}   {co['cost_per_parcel']}/parcel   "
          f"{co['cost_per_delivered']}/delivered")
        w(f"  CSAT proxy     : {s['csat_proxy']}/100")
        for r in s["by_service_level"]:
            w(f"    {r['level']:<10}: {r['parcels']:>4} parcels  {r['on_time_rate']:>5}% OT  "
              f"{r['avg_transit_hours']}h")
        if s["disruptions"]:
            for d in s["disruptions"]:
                w(f"  disruption: {d}")
        if run:
            w(f"  SimulationRun  : {run.pk}  " +
              ", ".join(f"{k}={v}" for k, v in sorted(run.record_counts.items())))
        for f in files:
            w(f"    {f}")
