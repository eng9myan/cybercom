"""
manage.py verify_rls [--table platform_einvoice_sequences]

Live end-to-end check that the PostgreSQL row-level-security policies actually
isolate tenants — run it in staging right after `apply_rls`.

What it does, all inside ONE transaction that is rolled back at the end (so it
writes nothing permanent):

  1. picks two random tenant UUIDs A and B
  2. sets app.current_tenant_id = A, inserts a probe row (tenant_id = A)
  3. sets it to B, inserts a probe row (tenant_id = B)
  4. as A: counts the two probe rows          -> must see exactly 1 (its own)
  5. as B: counts the two probe rows          -> must see exactly 1 (its own)
  6. clears the GUC: counts the two probe rows -> must see 0 (fail-closed)
  7. tries to UPDATE B's row while acting as A -> must affect 0 rows

Exit code 0 = all checks passed; non-zero (CommandError) = isolation is broken
or the policy is missing. PostgreSQL only.

Prereq: the DB role running this must NOT be superuser and must NOT have
BYPASSRLS (FORCE ROW LEVEL SECURITY covers table ownership, but a superuser
still bypasses everything). If checks 4-7 "pass" only because check 6 also
sees rows, the role is bypassing RLS — the command flags that.
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from platform.security.rls_ddl import POLICY_NAME, tenant_scoped_models

DEFAULT_TABLE = "platform_einvoice_sequences"


class _Rollback(Exception):
    """Sentinel — unwinds the probe transaction so nothing is persisted."""


def _guc() -> str:
    return getattr(settings, "TENANT_GUC_SETTING", "app.current_tenant_id")


class Command(BaseCommand):
    help = "Live-verify PostgreSQL RLS tenant isolation (writes nothing)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--table", default=DEFAULT_TABLE,
            help=f"tenant-scoped table to probe (default: {DEFAULT_TABLE})",
        )

    def handle(self, *args, **opts):
        if connection.vendor != "postgresql":
            raise CommandError(
                f"RLS is PostgreSQL-only; current backend is '{connection.vendor}'."
            )

        table = opts["table"]
        known = {m._meta.db_table for m in tenant_scoped_models()}
        if table not in known:
            raise CommandError(f"'{table}' is not a tenant-scoped table.")

        guc = _guc()
        a, b = str(uuid.uuid4()), str(uuid.uuid4())
        pa, pb = str(uuid.uuid4()), str(uuid.uuid4())
        failures: list[str] = []

        def set_tenant(cur, value):
            cur.execute("SELECT set_config(%s, %s, true)", [guc, value])

        try:
            with transaction.atomic(), connection.cursor() as cur:
                # policy present?
                cur.execute(
                    "SELECT 1 FROM pg_policies WHERE tablename = %s AND policyname = %s",
                    [table, POLICY_NAME],
                )
                if cur.fetchone() is None:
                    raise CommandError(
                        f"no policy '{POLICY_NAME}' on '{table}' — run `apply_rls` first."
                    )
                cur.execute(
                    "SELECT relrowsecurity, relforcerowsecurity "
                    "FROM pg_class WHERE relname = %s",
                    [table],
                )
                row = cur.fetchone()
                if not row or not row[0]:
                    raise CommandError(f"ROW LEVEL SECURITY is not enabled on '{table}'.")
                if not row[1]:
                    failures.append(f"{table}: FORCE ROW LEVEL SECURITY is off (owner bypasses)")

                # 2 + 3: insert one probe row per tenant, each under its own GUC.
                # _probe_columns is called freshly per row (not shared) so a
                # UNIQUE constraint on a probed column doesn't collide between
                # the two rows.
                set_tenant(cur, a)
                _insert_probe(cur, table, _probe_columns(cur, table), row_id=pa, tenant_id=a)
                set_tenant(cur, b)
                _insert_probe(cur, table, _probe_columns(cur, table), row_id=pb, tenant_id=b)

                probe_ids = (pa, pb)

                # 4: A sees only its own
                set_tenant(cur, a)
                seen_a = _count(cur, table, probe_ids)
                if seen_a != 1:
                    failures.append(f"tenant A saw {seen_a} probe rows, expected 1")

                # 5: B sees only its own
                set_tenant(cur, b)
                seen_b = _count(cur, table, probe_ids)
                if seen_b != 1:
                    failures.append(f"tenant B saw {seen_b} probe rows, expected 1")

                # 6: no tenant context -> nothing (fail-closed)
                set_tenant(cur, "")
                seen_none = _count(cur, table, probe_ids)
                if seen_none != 0:
                    failures.append(
                        f"with no tenant context {seen_none} probe rows were visible — "
                        f"expected 0 (role may have BYPASSRLS / be superuser)"
                    )

                # 7: A cannot touch B's row
                set_tenant(cur, a)
                cur.execute(
                    f'UPDATE "{table}" SET tenant_id = tenant_id WHERE id = %s', [pb]
                )
                if cur.rowcount != 0:
                    failures.append(
                        f"tenant A updated {cur.rowcount} of tenant B's rows — expected 0"
                    )

                raise _Rollback
        except _Rollback:
            pass
        except CommandError:
            raise
        except Exception as exc:  # e.g. a probe value violating an unforeseen
            # column constraint (see _probe_columns) — surface it as a clean
            # CommandError instead of an unhandled traceback; the transaction
            # rolls back either way, so no partial probe rows are left behind.
            raise CommandError(f"verify_rls probe failed on '{table}': {exc}") from exc

        if failures:
            self.stderr.write(self.style.ERROR(f"RLS VERIFY FAILED on '{table}':"))
            for f in failures:
                self.stderr.write(f"  - {f}")
            raise CommandError("tenant isolation is not enforced")

        self.stdout.write(self.style.SUCCESS(
            f"RLS VERIFY OK on '{table}': cross-tenant read + write blocked, "
            f"fail-closed with no tenant context."
        ))


def _probe_columns(cur, table) -> dict[str, str]:
    """NOT NULL columns without a default (besides id/tenant_id) that a probe
    INSERT must supply, mapped to a safe literal for their type. Called
    separately for each probe row (never shared) — the string literal below
    is randomized per call so a UNIQUE constraint on a probed column can't
    collide between the two tenants' rows."""
    cur.execute(
        """
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = %s
          AND is_nullable = 'NO'
          AND column_default IS NULL
          AND column_name NOT IN ('id', 'tenant_id')
        """,
        [table],
    )
    out: dict[str, str] = {}
    for name, dtype, max_len in cur.fetchall():
        if dtype in ("character varying", "text", "character"):
            probe = f"rls_probe_{uuid.uuid4().hex}"
            if max_len is not None and max_len < len(probe):
                probe = probe[: max(max_len, 1)]
            out[name] = f"'{probe}'"
        elif dtype in ("integer", "bigint", "smallint", "numeric", "double precision", "real"):
            out[name] = "0"
        elif dtype == "boolean":
            out[name] = "false"
        elif dtype in ("timestamp with time zone", "timestamp without time zone"):
            out[name] = "now()"
        elif dtype == "date":
            out[name] = "now()"
        elif dtype == "uuid":
            out[name] = f"'{uuid.uuid4()}'"
        elif dtype == "jsonb" or dtype == "json":
            out[name] = "'{}'"
        else:
            out[name] = "NULL"
    return out


def _insert_probe(cur, table, cols: dict[str, str], *, row_id: str, tenant_id: str):
    names = ["id", "tenant_id", *cols.keys()]
    values = [f"'{row_id}'", f"'{tenant_id}'", *cols.values()]
    quoted_names = ", ".join('"{}"'.format(n) for n in names)
    cur.execute(
        'INSERT INTO "{}" ({}) VALUES ({})'.format(
            table, quoted_names, ", ".join(values)
        )
    )


def _count(cur, table, ids) -> int:
    cur.execute(f'SELECT count(*) FROM "{table}" WHERE id IN (%s, %s)', list(ids))
    return cur.fetchone()[0]
