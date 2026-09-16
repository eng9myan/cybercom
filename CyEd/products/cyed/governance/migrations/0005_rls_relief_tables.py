"""
Extend Row-Level Security to the relief-teacher tables.

A CRT register holds a named external person's contact details, clearance
numbers and pay rate; a booking says who covered which absent teacher and what
it cost. Both are tenant data and neither had a policy.
"""

from django.db import migrations

NEW_RLS_TABLES = [
    "cyed_relief_teachers",
    "cyed_relief_availability",
    "cyed_relief_bookings",
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
        ("cyed_governance", "0004_rls_safety_tables"),
        ("cyed_substitution", "0003_reliefteacher_reliefbooking_reliefavailability"),
    ]

    operations = [migrations.RunPython(apply_rls, drop_rls)]
