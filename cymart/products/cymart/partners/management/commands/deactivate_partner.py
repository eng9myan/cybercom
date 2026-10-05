from django.core.management.base import BaseCommand, CommandError

from products.cymart.partners.models import Partner


class Command(BaseCommand):
    help = "Deactivates a partner's API key at once. Match by exact partner name, or by the key's first characters (key_prefix)."

    def add_arguments(self, parser):
        parser.add_argument("match", type=str, help="Partner name, or the start of the key (e.g. 'ds_live_AbC').")

    def handle(self, *args, **options):
        match = options["match"]
        qs = Partner.objects.filter(is_active=True)
        # the stored key_prefix is the first 12 characters of the key; accept a longer fragment or the whole key
        found = list(qs.filter(name=match))
        if not found and match.startswith("ds_live_"):
            found = list(qs.filter(key_prefix=match[:12]))
        if not found:
            raise CommandError(f"No active partner matches '{match}'.")
        for p in found:
            p.is_active = False
            p.save(update_fields=["is_active"])
            self.stdout.write(self.style.SUCCESS(f"Deactivated: {p.name} ({p.key_prefix}…)"))
