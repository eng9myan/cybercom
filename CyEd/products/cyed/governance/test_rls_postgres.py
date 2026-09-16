"""
Row-Level Security, exercised against the database that actually enforces it.

The policies are a no-op on SQLite, so until this file existed the tenant
isolation backstop had never been executed anywhere — the whole suite could
pass with RLS entirely broken. These tests skip unless the suite is running on
PostgreSQL (see `core/settings_test_pg`).

What is being checked is deliberately not the application layer. Every queryset
is already tenant-scoped by `TenantScopedModelViewSet`; the question here is
whether a **raw SQL query** — a reporting script, an ORM bug, an injection that
gets as far as executing SQL — can still read another school's rows. If it can,
RLS is decoration.
"""

import uuid

import pytest
from django.db import connection

pytestmark = pytest.mark.django_db(transaction=True)

TENANT_A = "11111111-1111-1111-1111-111111111111"
TENANT_B = "22222222-2222-2222-2222-222222222222"

pg_only = pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="Row-Level Security is a PostgreSQL feature; no-op on other backends.",
)


def _insert_student(tenant_id, first_name):
    """Insert directly, bypassing the ORM's tenant handling entirely."""
    student_id = uuid.uuid4()
    with connection.cursor() as cur:
        cur.execute("RESET app.current_tenant_id;")
        cur.execute(
            "INSERT INTO cyed_students "
            "(id, tenant_id, created_at, updated_at, first_name, last_name, "
            " student_number, year_level, enrolment_status, email, gender, "
            " usi, state_student_number, indigenous_status, country_of_birth, "
            " language_at_home, lbote, parent1_school_education, "
            " parent1_occupation_group, parent2_school_education, "
            " parent2_occupation_group, exit_reason, exit_destination) "
            "VALUES (%s, %s, now(), now(), %s, 'Test', '', 8, 'enrolled', '', '', "
            "        '', '', '9', '', '', false, '', '', '', '', '', '')",
            [student_id, tenant_id, first_name],
        )
    return student_id


def _rows_visible_as(tenant_id):
    with connection.cursor() as cur:
        if tenant_id is None:
            cur.execute("RESET app.current_tenant_id;")
        else:
            cur.execute("SET app.current_tenant_id = %s;", [str(tenant_id)])
        cur.execute("SELECT first_name FROM cyed_students ORDER BY first_name;")
        return [r[0] for r in cur.fetchall()]


@pg_only
def test_rls_is_enabled_and_forced_on_student_table():
    """
    FORCE matters: without it the policy is skipped for the table owner, which
    is exactly the role the application connects as.
    """
    with connection.cursor() as cur:
        cur.execute(
            "SELECT relrowsecurity, relforcerowsecurity "
            "FROM pg_class WHERE relname = 'cyed_students';"
        )
        enabled, forced = cur.fetchone()
    assert enabled, "RLS is not enabled on cyed_students."
    assert forced, "RLS is not FORCEd; the owning role bypasses every policy."


@pg_only
def test_a_superuser_connection_bypasses_rls_entirely():
    """
    The finding that makes the deploy check below necessary.

    PostgreSQL superusers ignore every row-level policy, FORCE included. Django
    defaults `DB_USER` to `postgres`, which is a superuser on a stock install —
    so a deployment that takes the default gets the policies created, reported
    as enabled and forced, and doing precisely nothing.

    This test asserts the bypass rather than pretending it away, because the
    protection is a property of the *role*, not of the schema.
    """
    with connection.cursor() as cur:
        cur.execute("SELECT usesuper FROM pg_user WHERE usename = current_user;")
        row = cur.fetchone()
    if not (row and row[0]):
        pytest.skip("Test connection is not a superuser; nothing to demonstrate.")

    _insert_student(TENANT_A, "AliceOfA")
    _insert_student(TENANT_B, "BobOfB")
    assert _rows_visible_as(TENANT_A) == ["AliceOfA", "BobOfB"]


@pg_only
def test_a_raw_query_cannot_read_another_schools_students():
    """
    The whole point: SQL that never touches the ORM cannot cross tenants —
    when the connection is an ordinary role, which is what production must use.

    Run under a purpose-made non-superuser rather than the test connection, so
    this asserts the policy is *correct* independently of how the suite happens
    to be connected.
    """
    import psycopg
    from django.conf import settings

    _insert_student(TENANT_A, "AliceOfA")
    _insert_student(TENANT_B, "BobOfB")

    db = settings.DATABASES["default"]
    role, password = "cyed_rls_probe", "probe-only"
    with connection.cursor() as cur:
        cur.execute(f"DROP ROLE IF EXISTS {role};")
        cur.execute(f"CREATE ROLE {role} LOGIN PASSWORD %s;", [password])
        cur.execute(f"GRANT SELECT ON cyed_students TO {role};")
        cur.execute(f"GRANT USAGE ON SCHEMA public TO {role};")

    try:
        with psycopg.connect(
            host=db["HOST"], port=db["PORT"], dbname=connection.settings_dict["NAME"],
            user=role, password=password, autocommit=True,
        ) as probe:
            with probe.cursor() as cur:
                # `SET` takes no bind parameters; `set_config` is its callable form.
                cur.execute("SELECT set_config('app.current_tenant_id', %s, false);", [TENANT_A])
                cur.execute("SELECT first_name FROM cyed_students ORDER BY first_name;")
                visible_to_a = [r[0] for r in cur.fetchall()]

                cur.execute("SELECT set_config('app.current_tenant_id', %s, false);", [TENANT_B])
                cur.execute("SELECT first_name FROM cyed_students ORDER BY first_name;")
                visible_to_b = [r[0] for r in cur.fetchall()]
    finally:
        with connection.cursor() as cur:
            cur.execute(f"REVOKE ALL ON cyed_students FROM {role};")
            cur.execute(f"REVOKE ALL ON SCHEMA public FROM {role};")
            cur.execute(f"DROP ROLE IF EXISTS {role};")

    assert visible_to_a == ["AliceOfA"], "School A could read another school's students."
    assert visible_to_b == ["BobOfB"], "School B could read another school's students."


@pg_only
def test_the_policy_covers_every_table_it_names():
    """A table listed in the migration but left unprotected is a silent hole."""
    from products.cyed.governance.rls import covered_tables

    tables = sorted(covered_tables())

    with connection.cursor() as cur:
        cur.execute(
            "SELECT relname FROM pg_class "
            "WHERE relname = ANY(%s) AND relrowsecurity AND relforcerowsecurity;",
            [tables],
        )
        protected = {r[0] for r in cur.fetchall()}

    missing = sorted(set(tables) - protected)
    assert not missing, f"Tables without enforced RLS: {missing}"


@pg_only
def test_health_data_is_isolated_too():
    """
    Health records are the most sensitive rows in the product, and were added
    to RLS in a later migration than the students table.
    """
    with connection.cursor() as cur:
        cur.execute(
            "SELECT relrowsecurity AND relforcerowsecurity FROM pg_class "
            "WHERE relname = 'cyed_immunisation_records';"
        )
        row = cur.fetchone()
    assert row and row[0], "Immunisation records are not protected by RLS."


@pg_only
def test_an_unset_tenant_sees_everything_by_design():
    """
    Migrations and platform-admin tooling run with no tenant set and must not
    be locked out of their own database. This is deliberate, and it is why the
    application middleware setting the GUC is load-bearing rather than
    optional — a request that fails to set it is not denied, it is unscoped.
    """
    _insert_student(TENANT_A, "AliceOfA")
    _insert_student(TENANT_B, "BobOfB")
    assert _rows_visible_as(None) == ["AliceOfA", "BobOfB"]
