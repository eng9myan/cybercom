"""verify_rls command — guardrails on SQLite, real isolation check on Postgres.

The Postgres path only runs when the test DB is actually PostgreSQL AND the
connection role does not bypass RLS; otherwise it self-skips. CI runs on SQLite,
so this mostly asserts the command refuses to give a false PASS there.
"""
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection


def test_verify_rls_refuses_sqlite():
    if connection.vendor == "postgresql":
        pytest.skip("postgres backend — covered by the enforcement test")
    with pytest.raises(CommandError):
        call_command("verify_rls")


def test_verify_rls_rejects_unknown_table():
    if connection.vendor != "postgresql":
        pytest.skip("needs postgres to get past the vendor check")
    with pytest.raises(CommandError):
        call_command("verify_rls", "--table", "not_a_real_table")


@pytest.mark.django_db
def test_verify_rls_passes_when_policies_are_applied():
    if connection.vendor != "postgresql":
        pytest.skip("RLS enforcement is a Postgres-only concern")

    # is the test role able to bypass RLS? if so this check is meaningless.
    with connection.cursor() as cur:
        cur.execute("SELECT current_setting('is_superuser')")
        if cur.fetchone()[0] == "on":
            pytest.skip("test DB role is superuser — RLS is bypassed, cannot verify")

    call_command("apply_rls", "--force")
    call_command("verify_rls")  # raises CommandError if isolation is broken
