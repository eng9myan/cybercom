"""
Extend Row-Level Security to the safety and absence tables.

Same reasoning as 0003, and the reason the coverage test in
`test_rls_coverage.py` exists: RLS lives in migrations nobody edits when a new
model lands, and the policies are a no-op on SQLite, so an unprotected table
looks perfectly healthy in the test suite.

Every table here names a child. An emergency roll entry says which children
were in the building and which were not accounted for; an action plan says what
a child is allergic to and what happens if they are exposed. These are among
the most sensitive rows in the product.
"""

from django.db import migrations

NEW_RLS_TABLES = [
    "cyed_health_action_plans",
    "cyed_emergency_drills",
    "cyed_emergency_roll_entries",
    "cyed_absence_explanations",
]

_POLICY = "tenant_isolation"


def apply_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cur:
        for table in NEW_RLS_TABLES:
            cur.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
            cur.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
            cur.execute(f"DROP POLICY IF EXISTS {_POLICY} ON {table};")
            cur.execute(
                f"CREATE POLICY {_POLICY} ON {table} USING ("
                "  current_setting('app.current_tenant_id', true) IS NULL"
                "  OR current_setting('app.current_tenant_id', true) = ''"
                "  OR tenant_id::text = current_setting('app.current_tenant_id', true)"
                ");"
            )


def drop_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cur:
        for table in NEW_RLS_TABLES:
            cur.execute(f"DROP POLICY IF EXISTS {_POLICY} ON {table};")
            cur.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
            cur.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")


class Migration(migrations.Migration):
    dependencies = [
        ("cyed_governance", "0003_rls_new_tables"),
        ("cyed_health", "0004_actionplan"),
        ("cyed_attendance", "0003_emergencydrill_emergencyrollentry"),
    ]

    operations = [migrations.RunPython(apply_rls, drop_rls)]
