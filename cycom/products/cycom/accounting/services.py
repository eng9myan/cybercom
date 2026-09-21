from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError as _DRFValidationError

from products.cycom.accounting.models import DepreciationEntry, FixedAsset, JournalEntry, JournalLine


class UnbalancedEntryError(_DRFValidationError):
    """Debits != credits. Subclasses DRF ValidationError so every posting
    path (ar_ap, pos, payroll, inventory, expenses) returns a clean 400
    instead of a 500, without each view needing its own try/except."""

    pass


class NonPostableAccountError(_DRFValidationError):
    """A journal line targets a group/header account (Account.is_postable=False)."""

    pass


@transaction.atomic
def post_journal_entry(
    *, tenant_id, date, reference, lines, currency="JOD", narration="", created_by="", company=None
):
    """
    lines: iterable of dicts {account, debit, credit, description(optional)}
    Creates a posted JournalEntry + JournalLines. Raises UnbalancedEntryError
    if debits != credits, or NonPostableAccountError if a line targets a
    group/header account — every GL posting in this system goes through here
    so double-entry integrity can't be bypassed by a sub-app forgetting to check.

    `company` is optional (multi-company is opt-in) — every existing caller
    that omits it keeps posting unscoped entries exactly as before.
    """
    lines = list(lines)

    non_postable = sorted(
        getattr(line["account"], "code", str(line["account"]))
        for line in lines
        if getattr(line.get("account"), "is_postable", True) is False
    )
    if non_postable:
        raise NonPostableAccountError(
            "Cannot post to group/header account(s): " + ", ".join(non_postable)
        )

    total_debit = sum(Decimal(line.get("debit", 0)) for line in lines)
    total_credit = sum(Decimal(line.get("credit", 0)) for line in lines)
    if total_debit != total_credit:
        raise UnbalancedEntryError(f"debit {total_debit} != credit {total_credit}")

    entry = JournalEntry.objects.create(
        tenant_id=tenant_id,
        date=date,
        reference=reference,
        currency=currency,
        status="posted",
        created_by=created_by,
        narration=narration,
        company=company,
    )
    for line in lines:
        JournalLine.objects.create(
            tenant_id=tenant_id,
            entry=entry,
            account=line["account"],
            debit=line.get("debit", 0),
            credit=line.get("credit", 0),
            currency=currency,
            description=line.get("description", ""),
        )
    return entry


@transaction.atomic
def run_depreciation(asset: FixedAsset, *, period) -> DepreciationEntry:
    """Post one month's straight-line depreciation for `asset`. `period` is
    any date within the target month — stored normalized to its first day."""
    if asset.status != "running":
        raise _DRFValidationError(f"Asset is '{asset.status}', must be 'running' to depreciate.")

    period = period.replace(day=1)
    if DepreciationEntry.objects.filter(asset=asset, period=period).exists():
        raise _DRFValidationError(f"Depreciation for {period} already recorded.")

    remaining = asset.depreciable_base - asset.accumulated_depreciation
    if remaining <= 0:
        raise _DRFValidationError("Asset is already fully depreciated.")

    amount = min(asset.monthly_depreciation, remaining)

    entry = post_journal_entry(
        tenant_id=asset.tenant_id,
        date=period,
        reference=f"DEPR-{asset.name}-{period.isoformat()}",
        lines=[
            {"account": asset.depreciation_expense_account, "debit": amount, "credit": 0},
            {"account": asset.accumulated_depreciation_account, "debit": 0, "credit": amount},
        ],
        narration=f"Monthly depreciation — {asset.name}",
    )
    dep_entry = DepreciationEntry.objects.create(
        tenant_id=asset.tenant_id, asset=asset, period=period, amount=amount, journal_entry=entry
    )

    if amount >= remaining:
        asset.status = "fully_depreciated"
        asset.save(update_fields=["status", "updated_at"])

    return dep_entry
