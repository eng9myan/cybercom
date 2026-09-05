"""
Seed a McDonald's-style QSR week into a cyshop demo tenant.

    python manage.py seed_qsr_sim --wipe
    python manage.py seed_qsr_sim --scenario promo_week --seed 7 --wipe
    python manage.py seed_qsr_sim --scenario supply_disruption --start-date 2026-09-01 --wipe

4 countries x 4 branches. Generates paid POS orders (counter / kiosk /
drive-thru / online) with kitchen timing, BOM-driven raw-goods consumption,
supplier deliveries and store crew, then rolls up the operational KPIs
(sales, wait times, service level, waste, days-of-cover, labour %).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.simulations.engine import QsrSimulator
from apps.simulations.kpis import QsrKpis
from apps.simulations.models import SimulationRun
from apps.simulations.scenarios import qsr as S
from apps.simulations.seeder import QsrSeeder


class Command(BaseCommand):
    help = "Seed a QSR (McDonald's-style) operating week into a cyshop demo tenant."

    def add_arguments(self, parser):
        parser.add_argument("--scenario", default="baseline", choices=sorted(S.VARIANTS),
                            help="which scenario variant to run")
        parser.add_argument("--seed", type=int, default=20260905)
        parser.add_argument("--start-date", default=None,
                            help="YYYY-MM-DD; default = 7 days ending yesterday")
        parser.add_argument("--days", type=int, default=7)
        parser.add_argument("--volume", type=float, default=1.0,
                            help="demand multiplier (0.2 = fast small run, 1.0 = full)")
        parser.add_argument("--countries", default=None,
                            help="comma list of ISO codes to limit to (default all: JO,SA,AE,EG)")
        parser.add_argument("--subdomain", default="qsr-demo")
        parser.add_argument("--tenant-name", default="McCybercom (QSR Demo)")
        parser.add_argument("--wipe", action="store_true",
                            help="delete this tenant's prior operational data first")
        parser.add_argument("--out", default=None, help="output dir for KPI files")
        parser.add_argument("--no-files", action="store_true", help="skip CSV/JSON export")
        parser.add_argument("--dry-run", action="store_true",
                            help="run the engine + KPIs and write files, but do not touch the DB")

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
            f"QSR simulation - {scenario}: {S.VARIANTS[scenario]['label']}"))
        self.stdout.write(f"  window   : {start} .. {start + timedelta(days=opts['days'] - 1)} "
                          f"({opts['days']} days)")
        self.stdout.write(f"  seed     : {opts['seed']}   volume: {opts['volume']}")

        countries = ([c.strip().upper() for c in opts["countries"].split(",")]
                     if opts["countries"] else None)
        sim = QsrSimulator(seed=opts["seed"], start_date=start, days=opts["days"],
                           variant=scenario, volume=opts["volume"], countries=countries)
        result = sim.run()
        self.stdout.write(f"  engine   : {len(result.orders)} orders, "
                          f"{len(result.deliveries)} deliveries, "
                          f"{len(result.lost_sales)} lost sales")

        kpis = QsrKpis(result)

        out_dir = Path(opts["out"]) if opts["out"] else (
            Path(settings.BASE_DIR).parent / "simulation_output"
            / f"qsr-{scenario}-{start:%Y%m%d}"
        )

        run = None
        if not opts["dry_run"]:
            run = SimulationRun.objects.create(
                scenario=f"qsr:{scenario}", seed=opts["seed"], start_date=start,
                days=opts["days"], status="RUNNING",
                parameters={"variant": scenario, "volume": opts["volume"],
                            "subdomain": opts["subdomain"]},
            )
            seeder = QsrSeeder(result, subdomain=opts["subdomain"],
                               tenant_name=opts["tenant_name"], run=run, stdout=self.stdout)
            try:
                if opts["wipe"]:
                    seeder.wipe()
                seeder.seed()
            except Exception as exc:   # noqa: BLE001 - record failure then re-raise
                run.status = "FAILED"
                run.error = repr(exc)
                run.save(update_fields=["status", "error", "updated_at", "version"])
                raise
            run.summary = kpis.summary()
            run.status = "COMPLETED"
            run.completed_at = timezone.now()
            run.save()

        summary = run.summary if run else kpis.summary()

        files = []
        if not opts["no_files"]:
            files = kpis.write_files(out_dir)

        self._print_summary(summary, files, run)

    # ------------------------------------------------------------------

    def _print_summary(self, s: dict, files: list[str], run):
        w = self.stdout.write
        t = s["totals"]
        sv = s["service"]
        w("")
        w(self.style.SUCCESS("=== KPI summary ==="))
        w(f"  net sales        : {t['net_sales']:,.2f} {S.REPORTING_CURRENCY}  "
          f"(gross {t['gross_sales']:,.2f}, tax {t['tax']:,.2f})")
        w(f"  orders           : {t['orders']:,}   avg check {t['avg_check']:.2f}   "
          f"units {t['units_sold']:,}")
        w(f"  lost sales       : {t['lost_sales_orders']:,}  "
          f"(~{t['lost_sales_est_revenue']:,.0f} {S.REPORTING_CURRENCY})")
        w(f"  service level    : {sv['on_time_rate']}% on time   "
          f"avg wait {sv['avg_wait_seconds']:.0f}s   p90 {sv['p90_wait_seconds']:.0f}s")
        for ch, c in sv["by_channel"].items():
            w(f"    {ch:<11}: {c['orders']:>6,} orders  {c['on_time_rate']:>5}% on time  "
              f"avg {c['avg_wait_seconds']:.0f}s")
        inv = s["inventory"]
        w(f"  waste            : {inv['waste_value']:,.2f} {S.REPORTING_CURRENCY}  "
          f"({inv['waste_pct_of_usage']}% of usage)")
        w(f"  tightest cover   : {inv['tightest_cover_days']} days at {inv['tightest_cover_at']}")
        w(f"  open POs at end  : {inv['open_purchase_orders']}   deliveries {inv['deliveries']}")
        lab = s["labor"]
        w(f"  labour           : {lab['weekly_labor_cost']:,.2f} {S.REPORTING_CURRENCY}  "
          f"({lab['labor_pct_of_net_sales']}% of net sales)")
        w(f"  CSAT proxy       : {s['csat_proxy']}/100")
        w("")
        w("  by country:")
        for c in s["by_country"]:
            w(f"    {c['name']:<22} {c['gross_sales']:>12,.0f}  {c['orders']:>7,} ord  "
              f"{c['on_time_rate']:>5}% OT  {c['avg_wait_seconds']:.0f}s")
        if s["disruptions"]:
            w("  disruptions:")
            for d in s["disruptions"]:
                w(f"    - {d}")
        if run:
            w("")
            w(f"  SimulationRun    : {run.pk}  tag {run.tag}")
            w(f"  records written  : " + ", ".join(
                f"{k}={v}" for k, v in sorted(run.record_counts.items())))
        if files:
            w("")
            w("  files:")
            for f in files:
                w(f"    {f}")
