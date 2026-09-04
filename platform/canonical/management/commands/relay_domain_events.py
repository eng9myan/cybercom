"""
manage.py relay_domain_events [--limit N] [--dry-run]

Moves unpublished `core_domain_events` rows onto the message broker and stamps
`published_at`. In production this is a Debezium/CDC pipe off the WAL or the
`canonical.relay_domain_events` celery task on a short beat; this command is
the manual / one-shot entry point and the ops hook.

Without a configured broker it logs each event and marks it published (so a
dev / CI run doesn't back the table up). Point it at a real publisher by
setting `settings.DOMAIN_EVENT_PUBLISHER = "dotted.path.to.callable"` taking
`(event) -> None`.
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from platform.canonical.events import relay, unpublished


class Command(BaseCommand):
    help = "Publish unpublished canonical domain events and stamp published_at."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=500)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        if opts["dry_run"]:
            n = unpublished(limit=opts["limit"]).count()
            relay(limit=opts["limit"], dry_run=True)
            self.stdout.write(self.style.SUCCESS(f"would publish {n} events."))
            return
        sent = relay(limit=opts["limit"])
        self.stdout.write(self.style.SUCCESS(f"published {sent} events."))
