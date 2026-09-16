"""
Extend Row-Level Security to the support-plan, sick bay and rubric-mark tables.

Support plans carry disability information, family consultation notes and a
student's own words — among the most sensitive rows in the product. A sick bay
visit says which child was unwell and who collected them. A rubric mark is a
named student's assessed performance.

Rubrics themselves (the criteria and levels) are also covered: they are
tenant-scoped school IP, and a school's marking standards are not something to
leak between customers even though they name no child.
"""

from django.db import migrations

NEW_RLS_TABLES = [
    "cyed_support_plans",
    "cyed_support_adjustments",
    "cyed_support_goals",
    "cyed_support_plan_reviews",
    "cyed_sick_bay_visits",
    "cyed_rubrics",
    "cyed_rubric_criteria",
    "cyed_rubric_levels",
    "cyed_rubric_marks",
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
        ("cyed_governance", "0006_rls_interviews_notices"),
        ("cyed_wellbeing", "0005_supportplan_supportgoal_supportadjustment_and_more"),
        ("cyed_health", "0005_sickbayvisit"),
        ("cyed_gradebook", "0002_rubric_assessment_rubric_rubriccriterion_rubriclevel_and_more"),
    ]

    operations = [migrations.RunPython(apply_rls, drop_rls)]
