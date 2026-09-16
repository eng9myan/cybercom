"""
Which tables Row-Level Security covers.

Discovered from the migrations rather than listed again here. RLS is applied by
a series of migrations, and every consumer that needs the full set — the
coverage test, the PostgreSQL enforcement test, the deploy check — previously
imported each migration by name. That meant three files to update whenever a
new RLS migration landed, and forgetting one of them is silent: the policy is
applied but nothing verifies it, or worse, the table is missed entirely and
everything still passes.

Scanning the package means adding a migration is enough.
"""

import importlib
import pkgutil

# Names a migration module may use to publish the tables it protects.
_TABLE_ATTRS = ("RLS_TABLES", "NEW_RLS_TABLES")


def covered_tables() -> set:
    """Every table named by any RLS migration in the governance app."""
    from products.cyed.governance import migrations as migrations_pkg

    tables = set()
    for module_info in pkgutil.iter_modules(migrations_pkg.__path__):
        # Only the RLS migrations publish these attributes; the rest are
        # ordinary schema migrations and are skipped by the getattr below.
        try:
            module = importlib.import_module(
                f"products.cyed.governance.migrations.{module_info.name}"
            )
        except Exception:
            continue
        for attr in _TABLE_ATTRS:
            tables.update(getattr(module, attr, []) or [])
    return tables
