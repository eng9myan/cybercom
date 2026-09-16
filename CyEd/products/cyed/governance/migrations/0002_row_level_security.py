"""
Defence-in-depth: PostgreSQL Row-Level Security on tenant-scoped tables.

The application layer already scopes every queryset by tenant (TenantScoped
viewsets). RLS adds a database-enforced backstop so that even a raw query or a
logic bug cannot cross tenants. Each request's tenant is published to the
session via `SET LOCAL app.current_tenant_id` (core.middleware.tenant), and the
policy below restricts every row to that tenant.

Runs only on PostgreSQL; on SQLite (dev/test) it is a no-op, so the suite is
unaffected. FORCE ROW LEVEL SECURITY makes the policy apply even to the table
owner (Django's DB role). A NULL/empty setting (platform-admin / migration
context) is allowed through so cross-tenant tooling still works.
"""

from django.db import migrations

RLS_TABLES = [
    "cyed_students",
    "cyed_guardians",
    "cyed_health_records",
    "cyed_medical_incidents",
    "cyed_wellbeing_notes",
    "cyed_wellbeing_checkins",
    "cyed_behaviour_incidents",
    "cyed_learner_profiles",
    "cyed_nccd_records",
    "cyed_student_bills",
    "cyed_installments",
    "cyed_attendance_marks",
]

_POLICY = "tenant_isolation"


def apply_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cur:
        for table in RLS_TABLES:
            cur.execute(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;')
            cur.execute(f'ALTER TABLE {table} FORCE ROW LEVEL SECURITY;')
            cur.execute(f'DROP POLICY IF EXISTS {_POLICY} ON {table};')
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
        for table in RLS_TABLES:
            cur.execute(f'DROP POLICY IF EXISTS {_POLICY} ON {table};')
            cur.execute(f'ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;')
            cur.execute(f'ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;')


class Migration(migrations.Migration):

    # Each dependency is the migration that actually creates a table this one
    # alters. They were pinned to each app's *initial* migration, but
    # `cyed_wellbeing_checkins` arrives in wellbeing 0002 — so `ALTER TABLE`
    # ran against a table that did not exist and `migrate` failed outright on
    # PostgreSQL. It passed everywhere it was tested only because the whole
    # operation is a no-op on SQLite.
    #
    # Pinned rather than `__latest__`: that alias re-resolves every time the
    # migration graph is built, so adding any migration to one of these apps
    # later would retroactively change what an *already-applied* migration
    # depended on, and Django rejects the history as inconsistent.
    dependencies = [
        ("cyed_governance", "0001_initial"),
        ("cyed_sis", "0002_classsection_campus_student_campus_and_more"),
        ("cyed_health", "0001_initial"),
        ("cyed_wellbeing", "0002_wellbeingcheckin"),
        ("cyed_billing", "0002_studentbill_campus"),
        ("cyed_attendance", "0001_initial"),
        ("cyed_compliance", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(apply_rls, drop_rls),
    ]
