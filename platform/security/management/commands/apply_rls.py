"""
manage.py apply_rls [--dry-run] [--teardown]

Applies (or prints, or removes) the PostgreSQL row-level-security policies for
every tenant-scoped table — see platform/security/rls_ddl.py.

Idempotent. Run it in the deploy pipeline after `migrate`. It refuses to run
against a non-PostgreSQL backend (nothing to do — SQLite has no RLS) and is a
no-op unless `settings.RLS_ENFORCED` is true, unless `--force` is given.

Deploy prerequisites (documented in docs/blueprint/specs/canonical-data-model-v1.md §2.1):
  * the application connects as a role that is NOT a superuser and does NOT
    have BYPASSRLS, and is NOT the table owner (FORCE RLS covers the owner too,
    but the app role must still not be superuser).
  * TenantIsolationMiddleware sets `app.current_tenant_id` per request.
"""
from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from platform.security.rls_ddl import rls_statements, rls_teardown_statements, tenant_scoped_models


class Command(BaseCommand):
    help = "Apply PostgreSQL RLS policies to tenant-scoped tables."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="print the SQL, apply nothing")
        parser.add_argument("--teardown", action="store_true", help="remove the policies instead")
        parser.add_argument("--force", action="store_true",
                            help="apply even when settings.RLS_ENFORCED is false")

    def handle(self, *args, **opts):
        stmts = rls_teardown_statements() if opts["teardown"] else rls_statements()
        n_models = len(tenant_scoped_models())

        if opts["dry_run"]:
            self.stdout.write(f"-- {n_models} tenant-scoped tables\n")
            for label, sql in stmts:
                self.stdout.write(f"-- {label}\n{sql}\n")
            return

        if connection.vendor != "postgresql":
            raise CommandError(
                f"RLS is PostgreSQL-only; current backend is '{connection.vendor}'. "
                f"Use --dry-run to see the SQL."
            )
        if not getattr(settings, "RLS_ENFORCED", False) and not opts["force"]:
            raise CommandError(
                "settings.RLS_ENFORCED is false. Set it true (recommended once the "
                "app DB role is non-superuser) or pass --force."
            )

        applied = 0
        with transaction.atomic():
            with connection.cursor() as cursor:
                for label, sql in stmts:
                    cursor.execute(sql)
                    applied += 1
        verb = "removed" if opts["teardown"] else "applied"
        self.stdout.write(self.style.SUCCESS(
            f"RLS {verb}: {applied} statements across {n_models} tables."
        ))
