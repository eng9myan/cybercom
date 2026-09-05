"""
Seed a 7-day hospital + clinic-network operating week into a cymed demo tenant.

    python manage.py seed_hospital_sim --wipe
    python manage.py seed_hospital_sim --scenario ed_surge --wipe
    python manage.py seed_hospital_sim --scenario imaging_ct_downtime --wipe
    python manage.py seed_hospital_sim --scenario nurse_shortage --wipe
    python manage.py seed_hospital_sim --scenario pharmacy_stockout --wipe

"Cymed US Specialty Hospital" (Amman) + 5 clinics. Generates emergency
arrivals -> triage -> disposition, outpatient clinic sessions, ED + direct
admissions with bed assignment / ICU / discharge, and lab / imaging / pharmacy
orders with turnaround; then rolls up the operational KPIs (ED wait + LWBS,
bed occupancy, ALOS, ICU census, order turnaround, clinic no-show / utilisation).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from products.cymed.simulations.engine import HospitalSimulator
from products.cymed.simulations.kpis import HospitalKpis
from products.cymed.simulations.models import SimulationRun
from products.cymed.simulations.scenarios import hospital as H
from products.cymed.simulations.seeder import HospitalSeeder


class Command(BaseCommand):
    help = "Seed a hospital + clinic-network operating week into a cymed demo tenant."

    def add_arguments(self, parser):
        parser.add_argument("--scenario", default="baseline", choices=sorted(H.VARIANTS))
        parser.add_argument("--seed", type=int, default=20260905)
        parser.add_argument("--start-date", default=None, help="YYYY-MM-DD")
        parser.add_argument("--days", type=int, default=7)
        parser.add_argument("--scale", type=float, default=1.0,
                            help="volume multiplier (0.15 = fast run, 1.0 = full hospital)")
        parser.add_argument("--slug", default="cymed-hospital-sim")
        parser.add_argument("--tenant-name", default="Cymed US Specialty Hospital (Demo)")
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

        scenario = opts["scenario"]
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Hospital simulation - {scenario}: {H.VARIANTS[scenario]['label']}"))
        self.stdout.write(f"  window : {start} .. {start + timedelta(days=opts['days'] - 1)}   "
                          f"seed {opts['seed']}   scale {opts['scale']}")

        sim = HospitalSimulator(seed=opts["seed"], start_date=start, days=opts["days"],
                                variant=scenario, scale=opts["scale"])
        result = sim.run()
        self.stdout.write(f"  engine : {len(result.ed_visits)} ED visits, "
                          f"{len(result.clinic_visits)} clinic visits, "
                          f"{len(result.stays)} admissions")

        kpis = HospitalKpis(result)
        out_dir = Path(opts["out"]) if opts["out"] else (
            Path(settings.BASE_DIR).parent / "simulation_output"
            / f"hospital-{scenario}-{start:%Y%m%d}")

        run = None
        if not opts["dry_run"]:
            seeder = HospitalSeeder(result, slug=opts["slug"], tenant_name=opts["tenant_name"],
                                    stdout=self.stdout)
            tid = seeder.ensure_tenant()
            run = SimulationRun.objects.create(
                tenant_id=tid,
                scenario=f"hospital:{scenario}", seed=opts["seed"], start_date=start,
                days=opts["days"], status="RUNNING",
                parameters={"variant": scenario, "scale": opts["scale"], "slug": opts["slug"]})
            seeder.set_run(run)
            try:
                if opts["wipe"]:
                    seeder.wipe()
                seeder.seed()
            except Exception as exc:   # noqa: BLE001
                run.status = "FAILED"
                run.error = repr(exc)
                run.save(update_fields=["status", "error", "updated_at"])
                raise
            run.summary = kpis.summary()
            run.status = "COMPLETED"
            run.completed_at = timezone.now()
            run.save()

        summary = run.summary if run else kpis.summary()
        files = [] if opts["no_files"] else kpis.write_files(out_dir)
        self._print(summary, files, run)

    def _print(self, s, files, run):
        w = self.stdout.write
        em, ip, od, cl = s["emergency"], s["inpatient"], s["orders"], s["clinics"]
        w("")
        w(self.style.SUCCESS("=== KPI summary ==="))
        w(f"  ED               : {em['visits']:,} visits   admit {em['admit_rate']}%   "
          f"LWBS {em['lwbs_rate']}%")
        w(f"  ED timeliness    : door->provider {em['avg_door_to_provider_min']:.0f}m   "
          f"door->dispo {em['avg_door_to_disposition_min']:.0f}m (p90 {em['p90_door_to_disposition_min']:.0f}m)")
        w(f"  inpatient        : {ip['admissions']:,} adm   census {ip['avg_daily_census']:.0f} "
          f"(peak {ip['peak_census']})   occ {ip['bed_occupancy_pct']}%   ALOS {ip['alos_days']}d")
        w(f"  ICU              : {ip['icu']['stays']} stays   census {ip['icu']['avg_daily_census']:.1f}   "
          f"occ {ip['icu']['occupancy_pct']}%")
        w(f"  boarding         : {ip['boarding']['count']} stays   "
          f"{ip['boarding']['total_boarding_hours']}h total")
        for k, v in od["by_kind"].items():
            w(f"  orders/{k:<10}: {v['count']:,}   TAT avg {v['avg_tat_min']:.0f}m  "
              f"p90 {v['p90_tat_min']:.0f}m   ({v['stat_count']} stat)")
        w(f"  clinics          : {cl['fulfilled']:,}/{cl['scheduled']:,} kept   "
          f"no-show {cl['no_show_rate']}%   walk-ins {cl['walk_ins']}   util {cl['utilization_pct']}%")
        w(f"  CSAT proxy       : {s['csat_proxy']}/100")
        w("")
        w("  by service line:")
        for sl in s["by_service_line"]:
            w(f"    {sl['display']:<16} ED {sl['ed_visits']:>4}  adm {sl['admissions']:>4}  "
              f"ALOS {sl['alos_days']}d  orders {sl['orders']}")
        if s["disruptions"]:
            w("  disruptions:")
            for d in s["disruptions"]:
                w(f"    - {d}")
        if run:
            w("")
            w(f"  SimulationRun    : {run.pk}  tag {run.tag}")
            w("  records          : " + ", ".join(f"{k}={v}" for k, v in sorted(run.record_counts.items())))
        for f in files:
            w(f"    {f}")
