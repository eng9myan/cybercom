"""
import_curriculum — load ACARA v9 outcomes into a tenant's registry.

    # bundled starter set (broad F-10 coverage)
    python manage.py import_curriculum --tenant <uuid>

    # the full licensed ACARA export (JSON array or CSV with a header row)
    python manage.py import_curriculum --tenant <uuid> --file acara_v9_full.csv

CSV/JSON columns: code, learning_area, year_level, strand, sub_strand,
content_description, achievement_standard, subject, state (only code +
learning_area are required). Idempotent — re-running updates existing codes.
"""

import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from products.cyed.curriculum.importer import import_outcomes

DEFAULT_TENANT = "11111111-1111-1111-1111-111111111111"
STARTER = Path(__file__).resolve().parents[2] / "data" / "acara_v9_starter.json"


def _load_rows(path: Path):
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".csv":
        return list(csv.DictReader(text.splitlines()))
    data = json.loads(text)
    if not isinstance(data, list):
        raise CommandError("JSON curriculum file must be an array of outcome objects.")
    return data


class Command(BaseCommand):
    help = "Import ACARA v9 curriculum outcomes for a tenant (bundled starter set or a file)."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", default=DEFAULT_TENANT)
        parser.add_argument("--file", default=None, help="Path to a JSON/CSV ACARA export.")
        parser.add_argument("--framework", default="ACARA v9")

    def handle(self, *args, **options):
        path = Path(options["file"]) if options["file"] else STARTER
        if not path.exists():
            raise CommandError(f"Curriculum file not found: {path}")

        rows = _load_rows(path)
        result = import_outcomes(options["tenant"], rows, framework=options["framework"])

        self.stdout.write(self.style.SUCCESS(
            f"Curriculum import for tenant {options['tenant']} from {path.name}: "
            f"{result['created']} created, {result['updated']} updated, "
            f"{result['skipped']} skipped."
        ))
        for err in result["errors"][:10]:
            self.stdout.write(self.style.WARNING(f"  row {err['row']}: {err['error']}"))
