"""
manage.py load_flavor_registry [--registry-only] [--packs-only]

Syncs docs/blueprint/schemas/flavor-registry.yaml (the full ~55-flavor
catalog) and every docs/blueprint/schemas/examples/*.flavor.yaml pack into
VerticalFlavor / LayoutTemplate rows. Idempotent — run on every deploy (or
trigger an on-demand refresh via VerticalFlavorViewSet.sync, admin-only).
"""
from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from platform.canonical import flavors


class Command(BaseCommand):
    help = "Sync the vertical-flavor registry and flavor packs into the DB."

    def add_arguments(self, parser):
        parser.add_argument(
            "--registry-only", action="store_true", help="Skip syncing *.flavor.yaml packs."
        )
        parser.add_argument(
            "--packs-only", action="store_true", help="Skip syncing flavor-registry.yaml."
        )

    def handle(self, *args, **opts):
        if not opts["packs_only"]:
            result = flavors.sync_registry()
            self.stdout.write(
                self.style.SUCCESS(
                    f"registry: {result['created']} created, {result['updated']} updated, "
                    f"{result['total']} total."
                )
            )
        if not opts["registry_only"]:
            try:
                result = flavors.sync_packs()
            except flavors.FlavorValidationError as exc:
                raise CommandError(str(exc)) from exc
            self.stdout.write(
                self.style.SUCCESS(
                    f"packs: {result['packs_synced']} synced "
                    f"({', '.join(result['keys']) or '-'})."
                )
            )
