"""
Load the Ready-ERP catalog (country / department / industry packs) from the
JSON files under platform/provisioning/packs/ into the catalog tables.

Idempotent: re-running updates existing rows in place (keyed on natural key
+ version), so editing a JSON pack and re-seeding just refreshes it.

    python manage.py seed_packs
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from platform.provisioning.models import CountryPack, DepartmentPack, IndustryTemplate

PACKS_DIR = Path(__file__).resolve().parent.parent.parent / "packs"


class Command(BaseCommand):
    help = "Seed/refresh the Ready-ERP country, department, and industry packs."

    def _load_dir(self, subdir):
        d = PACKS_DIR / subdir
        if not d.exists():
            return []
        return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.json"))]

    def handle(self, *args, **options):
        n_country = n_dept = n_ind = 0

        for data in self._load_dir("countries"):
            CountryPack.objects.update_or_create(
                code=data["code"],
                defaults={k: v for k, v in data.items() if k != "code"},
            )
            n_country += 1

        for data in self._load_dir("departments"):
            DepartmentPack.objects.update_or_create(
                key=data["key"],
                defaults={k: v for k, v in data.items() if k != "key"},
            )
            n_dept += 1

        for data in self._load_dir("industries"):
            IndustryTemplate.objects.update_or_create(
                key=data["key"],
                version=data.get("version", "1.0"),
                defaults={k: v for k, v in data.items() if k not in ("key", "version")},
            )
            n_ind += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {n_country} country, {n_dept} department, {n_ind} industry packs."
            )
        )
