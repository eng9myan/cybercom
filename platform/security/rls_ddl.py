"""
RLS DDL generation — the SQL that puts a PostgreSQL row-level-security policy
on every tenant-scoped table.

`rls_statements()` yields (label, sql) for each `TenantScopedMixin` model:
  ALTER TABLE ... ENABLE ROW LEVEL SECURITY
  ALTER TABLE ... FORCE ROW LEVEL SECURITY        -- so the table owner is bound too
  CREATE POLICY tenant_isolation ... USING (...) WITH CHECK (...)

The policy compares `tenant_id` against `NULLIF(current_setting('<guc>', true), '')::uuid`.
The `, true` (missing_ok) means a GUC that was never touched this session yields
NULL; `NULLIF(..., '')` additionally maps an *empty-string* value to NULL too —
`clear_tenant_guc()` (platform.security.rls, called by TenantContextMiddleware
after every tenant-scoped request) resets the GUC to `''` rather than unsetting
it, and on a pooled connection reused by a platform-admin (tenant_id=None)
request, `''` is exactly what the next request's queries see. Casting `''`
straight to `::uuid` raises a hard Postgres error on *every* query in that
request instead of returning zero rows — NULLIF closes that: either way,
`tenant_id = NULL` is false, so a connection with no tenant context sees **no
rows**, which is the fail-closed behaviour we want, without ever raising.

Applied by `manage.py apply_rls` (idempotent). Enforced only when
`settings.RLS_ENFORCED` is true AND the backend is PostgreSQL.
"""
from __future__ import annotations

from django.apps import apps
from django.conf import settings
from django.db import models

POLICY_NAME = "tenant_isolation"


def _guc() -> str:
    return getattr(settings, "TENANT_GUC_SETTING", "app.current_tenant_id")


def tenant_scoped_models() -> list[type[models.Model]]:
    """Every concrete, managed model that carries a `tenant_id` column via the
    platform TenantScopedMixin (or an equivalent non-null tenant_id field)."""
    out = []
    for model in apps.get_models():
        if model._meta.abstract or model._meta.proxy or not model._meta.managed:
            continue
        try:
            field = model._meta.get_field("tenant_id")
        except Exception:
            continue
        if isinstance(field, models.UUIDField):
            out.append(model)
    return sorted(out, key=lambda m: m._meta.db_table)


def rls_statements(guc: str | None = None) -> list[tuple[str, str]]:
    guc = guc or _guc()
    stmts: list[tuple[str, str]] = []
    for model in tenant_scoped_models():
        t = model._meta.db_table
        q = f'"{t}"'
        stmts.append((f"{t}: enable RLS", f"ALTER TABLE {q} ENABLE ROW LEVEL SECURITY;"))
        stmts.append((f"{t}: force RLS", f"ALTER TABLE {q} FORCE ROW LEVEL SECURITY;"))
        stmts.append((
            f"{t}: policy {POLICY_NAME}",
            f"DROP POLICY IF EXISTS {POLICY_NAME} ON {q};\n"
            f"CREATE POLICY {POLICY_NAME} ON {q}\n"
            f"  USING (tenant_id = NULLIF(current_setting('{guc}', true), '')::uuid)\n"
            f"  WITH CHECK (tenant_id = NULLIF(current_setting('{guc}', true), '')::uuid);",
        ))
    return stmts


def rls_teardown_statements() -> list[tuple[str, str]]:
    stmts: list[tuple[str, str]] = []
    for model in tenant_scoped_models():
        t = model._meta.db_table
        q = f'"{t}"'
        stmts.append((f"{t}: drop policy", f"DROP POLICY IF EXISTS {POLICY_NAME} ON {q};"))
        stmts.append((f"{t}: disable RLS", f"ALTER TABLE {q} DISABLE ROW LEVEL SECURITY;"))
    return stmts
