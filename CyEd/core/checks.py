"""
Deployment checks that catch silent security failures.

Registered with Django's check framework, so they run on `manage.py check
--deploy`, on `runserver`, and in CI — not as documentation someone is supposed
to remember.

Each check here exists because the failure it catches is **invisible**: the
system starts, serves traffic, passes its test suite, and is quietly not
protecting what it claims to protect.
"""

import os

from django.conf import settings
from django.core.checks import Error, Tags, Warning, register
from django.db import connection

# Only run the database checks when a database is actually reachable — `check`
# is expected to work without one (during image builds, for instance).
def _database_available() -> bool:
    try:
        connection.ensure_connection()
        return True
    except Exception:
        return False


@register(Tags.security, deploy=True)
def rls_role_is_not_superuser(app_configs, **kwargs):
    """
    PostgreSQL superusers bypass every row-level security policy, FORCE included.

    CyEd relies on RLS as the database-level backstop for tenant isolation —
    the thing that still holds when application scoping has a bug. Django's
    default `DB_USER` is `postgres`, which on a stock install is a superuser,
    so a deployment that takes the default creates all the policies, reports
    them as enabled and forced, and gets no protection whatsoever.

    Nothing observable distinguishes that state from a working one, which is
    why it has to be a check rather than a note in a runbook.
    """
    if connection.vendor != "postgresql" or not _database_available():
        return []

    try:
        with connection.cursor() as cur:
            cur.execute("SELECT usesuper FROM pg_user WHERE usename = current_user;")
            row = cur.fetchone()
    except Exception:
        return []

    if not (row and row[0]):
        return []

    return [
        Error(
            "The application connects to PostgreSQL as a superuser, which bypasses "
            "Row-Level Security completely.",
            hint=(
                "Every tenant-isolation policy is inactive on this connection. Create a "
                "dedicated non-superuser role that owns nothing and has only the "
                "privileges the app needs, and set DB_USER to it. Verify with: "
                "SELECT usesuper FROM pg_user WHERE usename = current_user;"
            ),
            id="cyed.E001",
        )
    ]


@register(Tags.security, deploy=True)
def rls_policies_are_present(app_configs, **kwargs):
    """
    Every table the RLS migrations name must actually carry an enforced policy.

    A table can lose one: restored from a dump taken with `--no-security-labels`,
    recreated by hand during an incident, or added to a model without being
    added to a migration. The schema still works; only the isolation is gone.
    """
    if connection.vendor != "postgresql" or not _database_available():
        return []

    try:
        from products.cyed.governance.rls import covered_tables

        expected = sorted(covered_tables())
    except Exception:
        return []
    try:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT relname FROM pg_class "
                "WHERE relname = ANY(%s) AND relrowsecurity AND relforcerowsecurity;",
                [expected],
            )
            protected = {r[0] for r in cur.fetchall()}
            cur.execute(
                "SELECT tablename FROM pg_tables WHERE tablename = ANY(%s);", [expected]
            )
            existing = {r[0] for r in cur.fetchall()}
    except Exception:
        return []

    missing = sorted((existing & set(expected)) - protected)
    if not missing:
        return []
    return [
        Error(
            f"{len(missing)} table(s) hold tenant data without enforced Row-Level "
            f"Security: {', '.join(missing)}.",
            hint="Re-run migrations, or apply the policy manually. Do not deploy without it.",
            id="cyed.E002",
        )
    ]


@register(Tags.security, deploy=True)
def atomic_requests_enabled(app_configs, **kwargs):
    """
    The tenant GUC is set with `SET LOCAL`, which only survives inside a
    transaction. Without ATOMIC_REQUESTS the setting is discarded immediately
    and every policy falls through to its "no tenant set" branch — which is
    permissive by design, so requests succeed and see everything.
    """
    db = settings.DATABASES.get("default", {})
    if db.get("ENGINE", "").endswith("postgresql") and not db.get("ATOMIC_REQUESTS"):
        return [
            Error(
                "DATABASES['default']['ATOMIC_REQUESTS'] is not enabled.",
                hint=(
                    "The per-request tenant setting uses SET LOCAL and is lost outside a "
                    "transaction, disabling Row-Level Security for every request."
                ),
                id="cyed.E003",
            )
        ]
    return []


@register(Tags.security, deploy=True)
def notification_providers_configured(app_configs, **kwargs):
    """
    An enabled-but-unwired notification channel fails loudly at send time — by
    design, so it can never report a false delivery. That is correct, and it
    also means a school believing it has SMS has none.

    Surfaced at deploy rather than discovered on the first absence.
    """
    problems = []
    for channel in ("SMS", "EMAIL"):
        enabled = os.environ.get(f"CYED_NOTIFY_{channel}_ENABLED") == "1"
        provider = os.environ.get(f"CYED_NOTIFY_{channel}_PROVIDER", "").strip()
        if enabled and not provider:
            problems.append(
                Error(
                    f"CYED_NOTIFY_{channel}_ENABLED is set but "
                    f"CYED_NOTIFY_{channel}_PROVIDER is empty.",
                    hint=(
                        f"Every {channel.lower()} will fail at send time. Configure a "
                        f"provider, or unset the ENABLED flag so messages queue honestly."
                    ),
                    id="cyed.E004",
                )
            )
        elif not enabled:
            problems.append(
                Warning(
                    f"{channel.title()} notifications are disabled; guardian alerts will "
                    f"only appear in-app.",
                    hint=(
                        "Absence alerts are a duty-of-care channel. A school running "
                        "without them must know that it is."
                    ),
                    id="cyed.W001",
                )
            )
    return problems


@register(Tags.security, deploy=True)
def payment_provider_configured(app_configs, **kwargs):
    """
    The default payment provider records offline money only. That is a real,
    reconciled workflow — most Australian schools take fees by BPAY — but a
    deployment that expected card payments should not discover it from a parent.
    """
    provider = os.environ.get("CYED_PAYMENT_PROVIDER", "manual")
    if provider in ("manual", "mock"):
        return [
            Warning(
                f"Payment provider is '{provider}': no card gateway is connected.",
                hint=(
                    "Fees can be recorded and reconciled, but families cannot pay online. "
                    "Set CYED_PAYMENT_PROVIDER once a merchant account exists."
                ),
                id="cyed.W002",
            )
        ]
    return []
