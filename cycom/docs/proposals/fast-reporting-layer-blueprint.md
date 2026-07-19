# Proposal: Pre-Aggregated Reporting Layer for Fast Ad-Hoc Pivots

**Status: proposal, not built.** Illustrative design — not wired into any
migration or `INSTALLED_APPS` yet.

## Why

Ad-hoc financial pivots (revenue by month by account, expense by department
by quarter) computed at query time by scanning raw `JournalLine` rows get
slower as transaction volume grows. A pre-aggregated summary table, refreshed
incrementally when journal entries post, keeps pivot queries fast regardless
of how many raw journal lines exist.

## Design

New model, refreshed on every `post_journal_entry` call (not on every read):

```python
# products/cycom/accounting/reporting_models.py
from django.db import models
from platform.common.models import BaseModel


class LedgerSummary(BaseModel):
    """
    One row per (account, year, month). Updated incrementally when a
    journal entry posts — never recomputed from scratch on read. Real
    pivots (revenue by month, expense by department) query THIS table,
    not JournalLine directly.
    """
    account = models.ForeignKey("cycom_accounting.Account", on_delete=models.CASCADE, related_name="summaries")
    year = models.PositiveIntegerField()
    month = models.PositiveSmallIntegerField()
    debit_total = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    credit_total = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    class Meta:
        db_table = "cycom_accounting_ledger_summary"
        unique_together = [("tenant_id", "account", "year", "month")]
        indexes = [models.Index(fields=["tenant_id", "year", "month"])]
```

Incremental update hook (called from `post_journal_entry`, additive — no
change to that function's existing balanced-entry guarantee):

```python
# products/cycom/accounting/reporting_services.py
from django.db.models import F
from products.cycom.accounting.reporting_models import LedgerSummary


def update_ledger_summary(journal_line):
    year, month = journal_line.entry.date.year, journal_line.entry.date.month
    summary, _ = LedgerSummary.objects.get_or_create(
        tenant_id=journal_line.tenant_id, account=journal_line.account, year=year, month=month,
    )
    LedgerSummary.objects.filter(id=summary.id).update(
        debit_total=F("debit_total") + journal_line.debit,
        credit_total=F("credit_total") + journal_line.credit,
    )
```

## Real gaps before this is production-ready

- Not yet wired into `post_journal_entry` — needs a deliberate call site added, plus a backfill migration/management command for existing historical journal lines.
- No reversal/void handling designed yet (what happens to the summary row if a journal entry is later reversed) — real accounting systems need this, not an afterthought.
- No API/serializer built yet for querying this table — would need its own read-only viewset once the write side is proven correct.
