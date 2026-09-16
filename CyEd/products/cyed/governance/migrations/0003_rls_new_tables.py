"""
Extend Row-Level Security to the tables added after 0002.

Every table below holds tenant-scoped personal data and was created without a
policy, so the database-level backstop protected the original tables and
nothing since. The application layer still scoped them correctly — this is
defence in depth, not the only defence — but the point of RLS is to survive a
logic bug or a raw query, and a table outside it has no such protection.

This is the kind of gap that widens silently: RLS lives in one migration that
nobody edits when a new model lands. Anything added after this migration needs
adding here too — see `test_rls_covers_sensitive_tables` in
`products/cyed/governance/test_rls_coverage.py`, which fails when a table
carrying student or staff PII is left out.
"""

from django.db import migrations

NEW_RLS_TABLES = [
    # Health — the most sensitive data in the product.
    "cyed_immunisation_records",
    "cyed_immunisation_doses",
    "cyed_medication_authorities",
    "cyed_medication_administrations",
    # Correspondence between school and home.
    "cyed_message_threads",
    "cyed_messages",
    "cyed_thread_participants",
    # Student records and lifecycle.
    "cyed_exam_candidates",
    "cyed_transfer_certificates",
    "cyed_campus_transfers",
    # Household finance.
    "cyed_credit_notes",
    "cyed_dunning_cases",
    "cyed_dunning_actions",
    "cyed_bill_line_items",
    "cyed_installment_payments",
    # Staff personal data.
    "cyed_hr_clearances",
    "cyed_hr_leave_entitlements",
    # Identifiers exposed to external systems.
    "cyed_sif_refids",
    # Circulation — links a named student to what they borrowed.
    "cyed_library_loans",
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
    # Pinned to the migrations that create these tables — see 0002 for why
    # `__latest__` is unsafe on an applied migration. A table added later gets
    # its own RLS migration; the coverage test fails until it does.
    dependencies = [
        ("cyed_governance", "0002_row_level_security"),
        ("cyed_health", "0003_immunisationrecord_medicationauthority_and_more"),
        ("cyed_messaging", "0001_initial"),
        ("cyed_exams", "0001_initial"),
        ("cyed_billing", "0004_dunningcase_dunningaction_creditnote_and_more"),
        ("cyed_hr", "0004_staffleave_balance_override_by_and_more"),
        ("cyed_sif", "0001_initial"),
        ("cyed_library", "0002_librarypolicy_loan_fine_amount_loan_fine_paid_on_and_more"),
        ("cyed_sis", "0006_student_exit_date_student_exit_destination_and_more"),
    ]

    operations = [migrations.RunPython(apply_rls, drop_rls)]
