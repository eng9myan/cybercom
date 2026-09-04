"""
manage.py backfill_audit_columns [--dry-run] [--app <label>]

M3 backfill for the M1 audit columns (canonical-data-model-v1.md §6.1b):

  * row_version: 0 -> 1 for every existing row. AddField gave historical rows
    the field default (0); a persisted row has been written at least once, so
    the optimistic-lock counter should start at 1. New rows already get 1 from
    BaseModel.save().
  * updated_by: NULL -> created_by, where the row has a creator but was never
    updated by a distinguishable actor. The row's last-known actor is whoever
    created it.

`created_by` is NOT backfilled — a row created before the actor-population
code (or by a system path) legitimately has no actor. Per §1.2 `created_by`
and `updated_by` stay nullable permanently; this only tightens what we CAN
attribute.

Idempotent — safe to run repeatedly and in every environment as part of a
deploy. Uses `.update()` (no save(), no row_version re-bump). If RLS is
enforced, run as a role that is not subject to the tenant policy (the
migration/maintenance role), or per-tenant inside `tenant_context`.
"""
from __future__ import annotations

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F


def _audit_models(app_label: str | None):
    for model in django_apps.get_models():
        if model._meta.abstract or model._meta.proxy or not model._meta.managed:
            continue
        field_names = {f.name for f in model._meta.get_fields()}
        if not {"row_version", "created_by", "updated_by"} <= field_names:
            continue
        if app_label and model._meta.app_label != app_label:
            continue
        yield model


class Command(BaseCommand):
    help = "Backfill row_version and updated_by on existing BaseModel rows (M3)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="report counts, change nothing")
        parser.add_argument("--app", default=None, help="limit to one app label")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        models = list(_audit_models(opts["app"]))
        total_rv = total_ub = 0

        for model in models:
            base = model._default_manager.all()
            rv_qs = base.filter(row_version=0)
            ub_qs = base.filter(updated_by__isnull=True, created_by__isnull=False)
            rv_n, ub_n = rv_qs.count(), ub_qs.count()
            if not (rv_n or ub_n):
                continue
            total_rv += rv_n
            total_ub += ub_n
            self.stdout.write(
                f"{model._meta.label}: row_version+{rv_n}  updated_by<-created_by {ub_n}"
            )
            if not dry:
                with transaction.atomic():
                    if ub_n:
                        ub_qs.update(updated_by=F("created_by"))
                    if rv_n:
                        # re-filter: the ub update above did not touch row_version
                        model._default_manager.filter(row_version=0).update(row_version=1)

        verb = "would set" if dry else "set"
        self.stdout.write(self.style.SUCCESS(
            f"{verb} row_version on {total_rv} rows, updated_by on {total_ub} rows "
            f"across {len(models)} models."
        ))
