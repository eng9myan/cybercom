import datetime

from django.core.management.base import BaseCommand
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from products.cymart.partners.models import PartnerCallLog


class Command(BaseCommand):
    help = "Usage per partner and month (calls and items checked). The basis for per-call billing or a usage statement."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=90, help="Look back this many days (default 90).")

    def handle(self, *args, **options):
        since = timezone.now() - datetime.timedelta(days=options["days"])
        rows = (
            PartnerCallLog.objects.filter(created_at__gte=since)
            .annotate(month=TruncMonth("created_at"))
            .values("partner__name", "month")
            .annotate(calls=Count("id"), items=Sum("item_count"))
            .order_by("partner__name", "month")
        )
        if not rows:
            self.stdout.write("No usage in this period.")
            return
        self.stdout.write(f"{'Partner':<32} {'Month':<9} {'Calls':>9} {'Items':>10}")
        for r in rows:
            self.stdout.write(f"{r['partner__name'][:31]:<32} {r['month']:%Y-%m}   {r['calls']:>9,} {r['items'] or 0:>10,}")
