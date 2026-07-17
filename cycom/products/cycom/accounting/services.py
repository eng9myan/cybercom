from decimal import Decimal

from django.db import transaction

from products.cycom.accounting.models import JournalEntry, JournalLine


class UnbalancedEntryError(Exception):
    pass


@transaction.atomic
def post_journal_entry(*, tenant_id, date, reference, lines, currency="JOD", narration="", created_by=""):
    """
    lines: iterable of dicts {account, debit, credit, description(optional)}
    Creates a posted JournalEntry + JournalLines. Raises UnbalancedEntryError
    if debits != credits — every GL posting in this system goes through here
    so double-entry integrity can't be bypassed by a sub-app forgetting to check.
    """
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
