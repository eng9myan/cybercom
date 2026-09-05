"""RLS DDL generation + apply_rls guardrails. SQL is asserted as strings
(runs on SQLite); actual policy enforcement is a Postgres-only integration
concern, exercised in the deploy environment."""
import io

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection, models as djm

from platform.security.rls_ddl import (
    POLICY_NAME,
    rls_statements,
    rls_teardown_statements,
    tenant_scoped_models,
)


def test_tenant_scoped_models_are_uuid_tenant_id_only():
    scoped = tenant_scoped_models()
    assert scoped, "no tenant-scoped models discovered"
    for m in scoped:
        f = m._meta.get_field("tenant_id")
        assert isinstance(f, djm.UUIDField), f"{m._meta.db_table}.tenant_id is {type(f).__name__}"
    # a table that is NOT tenant-scoped must be absent (sanity: no false positives)
    assert "django_session" not in {m._meta.db_table for m in scoped}
    assert "core_orders" not in {m._meta.db_table for m in scoped}  # canonical model not built yet


def test_rls_statements_shape():
    stmts = rls_statements()
    assert stmts, "no tenant-scoped models found"
    sql_by_label = dict(stmts)

    # every table gets enable + force + policy
    tables = {m._meta.db_table for m in tenant_scoped_models()}
    for t in tables:
        assert f"ALTER TABLE \"{t}\" ENABLE ROW LEVEL SECURITY;" == sql_by_label[f"{t}: enable RLS"]
        assert f"ALTER TABLE \"{t}\" FORCE ROW LEVEL SECURITY;" == sql_by_label[f"{t}: force RLS"]
        policy = sql_by_label[f"{t}: policy {POLICY_NAME}"]
        assert f"CREATE POLICY {POLICY_NAME} ON \"{t}\"" in policy
        assert "NULLIF(current_setting('app.current_tenant_id', true), '')::uuid" in policy
        assert "USING (" in policy and "WITH CHECK (" in policy
        # missing_ok=true -> unset GUC = NULL; NULLIF(..., '') -> a *cleared*
        # (empty-string) GUC is also NULL -> tenant_id = NULL -> no rows
        # (fail closed), and neither case raises on the ::uuid cast.


def test_rls_statements_honour_custom_guc(settings):
    settings.TENANT_GUC_SETTING = "app.tid"
    a_table = tenant_scoped_models()[0]._meta.db_table
    policy = dict(rls_statements())[f"{a_table}: policy {POLICY_NAME}"]
    assert "NULLIF(current_setting('app.tid', true), '')::uuid" in policy
    assert "current_setting('app.current_tenant_id'" not in policy


def test_teardown_is_the_inverse():
    down = dict(rls_teardown_statements())
    for t in {m._meta.db_table for m in tenant_scoped_models()}:
        assert f"DROP POLICY IF EXISTS {POLICY_NAME} ON \"{t}\";" == down[f"{t}: drop policy"]
        assert f"ALTER TABLE \"{t}\" DISABLE ROW LEVEL SECURITY;" == down[f"{t}: disable RLS"]


def test_apply_rls_dry_run_prints_sql():
    out = io.StringIO()
    call_command("apply_rls", "--dry-run", stdout=out)
    text = out.getvalue()
    assert "ENABLE ROW LEVEL SECURITY" in text
    assert f"CREATE POLICY {POLICY_NAME}" in text


def test_apply_rls_refuses_sqlite():
    if connection.vendor == "postgresql":
        pytest.skip("postgres backend — the refusal path is unreachable, covered by test_rls_verify.py")
    # backend is sqlite in tests -> hard error, never a silent no-op
    with pytest.raises(CommandError):
        call_command("apply_rls", "--force")


def test_apply_rls_refuses_without_enforced_flag(settings):
    settings.RLS_ENFORCED = False
    with pytest.raises(CommandError):
        call_command("apply_rls")
