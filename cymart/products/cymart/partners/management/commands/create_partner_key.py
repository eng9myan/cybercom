from django.core.management.base import BaseCommand

from products.cymart.partners.models import Partner


class Command(BaseCommand):
    help = "Creates a Partner and prints its API key once — for sandbox/demo use."

    def add_arguments(self, parser):
        parser.add_argument("name", type=str, help="Partner display name, e.g. 'Talabat (sandbox)'.")

    def handle(self, *args, **options):
        partner, raw_key = Partner.create_with_key(options["name"])
        self.stdout.write(self.style.SUCCESS(f"Created partner: {partner.name} ({partner.id})"))
        self.stdout.write("")
        self.stdout.write("API key (shown once, store it now):")
        self.stdout.write(self.style.WARNING(raw_key))
        self.stdout.write("")
        self.stdout.write("Use it as:  X-API-Key: " + raw_key)
