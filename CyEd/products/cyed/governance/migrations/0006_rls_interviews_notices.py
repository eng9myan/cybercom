"""
Extend Row-Level Security to the interview and notice tables.

An interview booking names a child and the teacher their family chose to see;
a notice can be addressed to one campus's year group. Both are tenant data.
"""

from django.db import migrations

NEW_RLS_TABLES = [
    "cyed_interview_rounds",
    "cyed_interview_slots",
    "cyed_interview_bookings",
    "cyed_notices",
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
        ("cyed_governance", "0005_rls_relief_tables"),
        ("cyed_meetings", "0002_interviewround_interviewslot_interviewbooking_and_more"),
        ("cyed_school", "0003_notice"),
    ]

    operations = [migrations.RunPython(apply_rls, drop_rls)]
