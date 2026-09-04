"""
manage.py relay_domain_events [--limit N] [--dry-run]

Moves unpublished `core_domain_events` rows onto the message broker and stamps
`published_at`. In production this is a Debezium/CDC pipe off the WAL; this
command is the fallback / local relay and the test hook.

Without a configured broker it logs each event and marks it published (so a
dev / CI run doesn't back the table up). Point it at a real publisher by
setting `settings.DOMAIN_EVENT_PUBLISHER = "dotted.path.to.callable"` taking
`(event) -> None`.
"""
from __future__ import annotations

import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.module_loading import import_string

from platform.canonical.events import unpublished

logger = logging.getLogger("platform.canonical.relay")


class Command(BaseCommand):
    help = "Publish unpublished canonical domain events and stamp published_at."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=500)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        publisher = None
        path = getattr(settings, "DOMAIN_EVENT_PUBLISHER", None)
        if path:
            publisher = import_string(path)

        events = list(unpublished(limit=opts["limit"]))
        sent = 0
        for e in events:
            if opts["dry_run"]:
                self.stdout.write(f"would publish {e.event_type} <{e.aggregate_type}:{e.aggregate_id}>")
                continue
            if publisher:
                publisher(e)
            else:
                logger.info("domain-event %s %s %s", e.event_type, e.aggregate_type, e.aggregate_id)
            e.published_at = timezone.now()
            e.save(update_fields=["published_at"])
            sent += 1

        verb = "would publish" if opts["dry_run"] else "published"
        self.stdout.write(self.style.SUCCESS(f"{verb} {len(events) if opts['dry_run'] else sent} events."))
