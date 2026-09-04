"""
manage.py dump_pii_map [--json]

Prints every encrypted (PII/PHI) field registered via
platform.common.fields.EncryptedText — the data map that feeds the DPIA, the
residency data-flow lint (`H` C1), and DSAR tooling.
"""
from __future__ import annotations

import json

from django.core.management.base import BaseCommand

from platform.common.pii_registry import CLASSES, registered_pii_fields


class Command(BaseCommand):
    help = "List all per-tenant-encrypted PII/PHI model fields."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true")

    def handle(self, *args, **opts):
        fields = registered_pii_fields()
        if opts["json"]:
            self.stdout.write(json.dumps(
                [f.__dict__ for f in fields], indent=2, ensure_ascii=False
            ))
            return
        if not fields:
            self.stdout.write("no encrypted PII/PHI fields registered.")
            return
        by_class: dict[str, list] = {}
        for f in fields:
            by_class.setdefault(f.classification, []).append(f)
        for cls, group in sorted(by_class.items()):
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n{cls} — {CLASSES.get(cls, '')}"))
            for f in group:
                bidx = "  [blind-indexed]" if f.blind_indexed else ""
                self.stdout.write(f"  {f.model_label}.{f.field_name}{bidx}")
        self.stdout.write(f"\n{len(fields)} encrypted field(s) total.")
