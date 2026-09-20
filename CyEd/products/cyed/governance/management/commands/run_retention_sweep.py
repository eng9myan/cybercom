"""
Automated data retention / disposal sweep.

    python manage.py run_retention_sweep                 # dry run, reports only
    python manage.py run_retention_sweep --apply          # actually acts
    python manage.py run_retention_sweep --apply --tenant <uuid>

Intended to run on a schedule (cron / k8s CronJob) against production, dry-run
by default so a misconfigured window is caught in a report, not by finding
out real data disappeared.
"""
from django.core.management.base import BaseCommand

from products.cyed.governance.retention import RETENTION_POLICIES, run_all


class Command(BaseCommand):
    help = "Sweep for records past their retention window and de-identify/purge them."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Actually act (default: dry run).")
        parser.add_argument("--tenant", default=None, help="Limit to one tenant UUID.")

    def handle(self, *args, **options):
        apply = options["apply"]
        tenant_id = options["tenant"]

        self.stdout.write(self.style.WARNING(
            f"Retention sweep — {'APPLYING' if apply else 'DRY RUN (pass --apply to act)'}"
        ))
        for category, policy in RETENTION_POLICIES.items():
            window = f"{policy.get('years', 0)}y" if "years" in policy else f"{policy.get('days', 0)}d"
            self.stdout.write(f"  {category}: retention window {window}")

        results = run_all(tenant_id, apply=apply)
        for r in results:
            verb = "purged/de-identified" if apply else "would act on"
            self.stdout.write(f"{r.category}: matched {r.matched}, {verb} {r.acted}")

        total_matched = sum(r.matched for r in results)
        if not apply and total_matched:
            self.stdout.write(self.style.WARNING(
                f"{total_matched} record(s) matched. Re-run with --apply to act."
            ))
        self.stdout.write(self.style.SUCCESS("Retention sweep complete."))
