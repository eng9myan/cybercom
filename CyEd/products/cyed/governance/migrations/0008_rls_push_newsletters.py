"""
Extend Row-Level Security to the push-device and newsletter tables.

A push token is a credential: whoever holds it can send notifications to that
device. A newsletter carries the school's own communications and its audience
targeting. Neither should be readable across tenants.
"""

from django.db import migrations

NEW_RLS_TABLES = [
    "cyed_push_devices",
    "cyed_newsletters",
    # Pre-dates this migration and was never covered: a participation names a
    # child, whether their family consented, and what they were charged. Caught
    # by the coverage test when excursions gave it more to hold.
    "cyed_event_participations",
    "cyed_events",
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
        ("cyed_governance", "0007_rls_plans_rubrics_sickbay"),
        ("cyed_notifications", "0003_newsletter_pushdevice"),
        ("cyed_events", "0002_event_charge_students_event_departs_at_and_more"),
    ]

    operations = [migrations.RunPython(apply_rls, drop_rls)]
