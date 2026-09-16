"""Gapless per-tenant/per-document-type numbering (audit A-4).

`allocate_document_number()` is the single sanctioned way to consume a number
from a `DocumentSequence`. It runs inside the caller's transaction and takes a
`SELECT ... FOR UPDATE` row lock, so two requests issuing the same document
type concurrently serialise on the counter row — no duplicate, no skipped
value. A document type with no configured row gets one auto-created from
`SEQUENCE_DEFAULTS` on first use.
"""

from django.db import transaction
from django.utils import timezone

from products.cycom.accounting.models import DocumentSequence

# Per-doc_type defaults used when a tenant hits a document type for the first
# time. `pattern` is a str.format template over prefix/seq/yyyy/yy/mm.
SEQUENCE_DEFAULTS = {
    "customer_invoice": {"prefix": "INV-", "pattern": "{prefix}{yyyy}-{seq}", "period_scope": "yearly"},
    "vendor_bill": {"prefix": "BILL-", "pattern": "{prefix}{yyyy}-{seq}", "period_scope": "yearly"},
    "customer_credit_note": {"prefix": "CN-", "pattern": "{prefix}{yyyy}-{seq}", "period_scope": "yearly"},
    "vendor_credit_note": {"prefix": "DN-", "pattern": "{prefix}{yyyy}-{seq}", "period_scope": "yearly"},
    "pos_order": {"prefix": "POS-", "pattern": "{prefix}{yyyy}{mm}-{seq}", "padding": 5, "period_scope": "monthly"},
    "payroll_run": {"prefix": "PR-", "pattern": "{prefix}{yyyy}-{seq}", "padding": 3, "period_scope": "yearly"},
}

# The invoice_type stored on ar_ap.Invoice maps 1:1 onto a sequence doc_type.
INVOICE_TYPE_TO_DOC_TYPE = {
    "customer": "customer_invoice",
    "vendor": "vendor_bill",
    "customer_credit_note": "customer_credit_note",
    "vendor_credit_note": "vendor_credit_note",
}

# Realm/session roles allowed to override the auto number with a manual one.
OVERRIDE_ROLES = {"platform_admin", "tenant_admin", "finance_manager", "accountant", "chief_accountant"}


def _period_key(scope, when):
    if scope == DocumentSequence.PERIOD_YEARLY:
        return f"{when:%Y}"
    if scope == DocumentSequence.PERIOD_MONTHLY:
        return f"{when:%Y-%m}"
    return ""


def _format(seq, value, when):
    return seq.pattern.format(
        prefix=seq.prefix,
        seq=str(value).zfill(seq.padding),
        yyyy=f"{when:%Y}",
        yy=f"{when:%y}",
        mm=f"{when:%m}",
    )


@transaction.atomic
def allocate_document_number(tenant_id, doc_type, *, when=None):
    """Consume and return the next number for (tenant_id, doc_type).

    `when` (a date) selects the period bucket for period-scoped sequences;
    defaults to today. Must be called inside a DB transaction that also writes
    the document, so an allocated number is never orphaned by a later rollback.
    """
    when = when or timezone.localdate()
    defaults = SEQUENCE_DEFAULTS.get(doc_type, {})

    # Ensure the row exists (racing creates collide on the unique constraint —
    # get_or_create swallows that), then lock it for the read-modify-write.
    DocumentSequence.objects.get_or_create(
        tenant_id=tenant_id,
        doc_type=doc_type,
        defaults={
            "prefix": defaults.get("prefix", ""),
            "pattern": defaults.get("pattern", DocumentSequence._meta.get_field("pattern").default),
            "padding": defaults.get("padding", 5),
            "period_scope": defaults.get("period_scope", DocumentSequence.PERIOD_YEARLY),
        },
    )
    seq = DocumentSequence.objects.select_for_update().get(tenant_id=tenant_id, doc_type=doc_type)

    period_key = _period_key(seq.period_scope, when)
    if period_key != seq.period_key:
        seq.period_key = period_key
        seq.next_value = 1

    value = seq.next_value
    seq.next_value = value + 1
    seq.save(update_fields=["period_key", "next_value", "row_version", "updated_at"])
    return _format(seq, value, when)


def can_override_document_number(request):
    """True if the caller may supply a manual document number instead of the
    auto-allocated one. Reads the normalised role list the auth middleware puts
    on `request.user_session` (dev + prod both populate it)."""
    session = getattr(request, "user_session", None) or {}
    roles = set(session.get("roles", []))
    if roles & OVERRIDE_ROLES:
        return True
    claims = getattr(request, "auth_claims", None) or {}
    realm_roles = set(claims.get("realm_access", {}).get("roles", []))
    return bool(realm_roles & OVERRIDE_ROLES)
