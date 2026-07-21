"""
CyID ecosystem, Phase 7 — CyID Wallet (stored value). Keyed to
PersonIdentity (Phase 2's cross-tenant identity), not to any single
tenant — the whole point of the CyID wallet is that it works the same
regardless of which product/tenant the person is transacting in (a
Cymed pharmacy pickup, a Cyshop retail order — see Phase 8).

Deliberately does NOT post through products.cycom.accounting.services'
post_journal_entry(): that's Cycom's own internal GL engine, and Wallet
is meant to be usable by every product (Cymed, Cyshop, Cycom alike) —
depending on one product's accounting internals from this shared platform
layer would be a real layering violation (cyshop has no such engine at
all). Instead this is its own minimal, real, atomic ledger: an
append-only WalletLedgerEntry per transaction plus a denormalized running
balance on WalletAccount, kept consistent via select_for_update — the
same "immutable ledger + cached balance" pattern most real stored-value
systems use, just not routed through Cycom's specific GL tables.
"""

from django.db import models

from platform.common.models import PlatformModel
from platform.cyidentity.models import PersonIdentity


class WalletEntryType(models.TextChoices):
    TOPUP = "topup", "Top-Up"
    DEBIT = "debit", "Debit"
    REFUND = "refund", "Refund"
    ADJUSTMENT = "adjustment", "Adjustment"


class WalletAccount(PlatformModel):
    person = models.ForeignKey(PersonIdentity, on_delete=models.CASCADE, related_name="wallets")
    currency = models.CharField(max_length=3)  # ISO 4217, e.g. "USD", "JOD"
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = "platform_wallet_accounts"
        unique_together = [("person", "currency")]
        indexes = [
            models.Index(fields=["person", "currency"]),
        ]

    def __str__(self) -> str:
        return f"Wallet({self.person.cyid}, {self.currency}, {self.balance})"


class WalletLedgerEntry(PlatformModel):
    wallet = models.ForeignKey(WalletAccount, on_delete=models.CASCADE, related_name="entries")
    entry_type = models.CharField(max_length=20, choices=WalletEntryType.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)  # always positive; entry_type gives sign
    balance_after = models.DecimalField(max_digits=14, decimal_places=2)
    reference = models.CharField(max_length=255, blank=True)  # e.g. an order/invoice id from the calling product
    created_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "platform_wallet_ledger_entries"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"WalletEntry({self.entry_type}, {self.amount}, wallet={self.wallet_id})"


class CheckoutReceiptLineType(models.TextChoices):
    CYMED_ORDER = "cymed_order", "Cymed Order Payment"
    CYSHOP_ORDER = "cyshop_order", "Cyshop Retail Order"


class CheckoutReceipt(PlatformModel):
    """
    CyID ecosystem, Phase 8 — one cross-network checkout: a single wallet
    debit paying for line items spanning multiple products (e.g. a Cymed
    pharmacy pickup + a Cyshop retail item in one cart). Lives in
    platform.wallet (product-agnostic — any product's items can appear as
    a line here) even though the orchestrating service that BUILDS one of
    these lives in cymed (it's the one that needs to import cymed's own
    Order model directly; see products.cymed.core.commerce.checkout).
    """

    person = models.ForeignKey(PersonIdentity, on_delete=models.PROTECT, related_name="checkout_receipts")
    wallet_ledger_entry = models.ForeignKey(
        WalletLedgerEntry, on_delete=models.PROTECT, related_name="checkout_receipt"
    )
    currency = models.CharField(max_length=3)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        db_table = "platform_checkout_receipts"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"CheckoutReceipt({self.person.cyid}, {self.total_amount} {self.currency})"


class CheckoutReceiptLine(PlatformModel):
    receipt = models.ForeignKey(CheckoutReceipt, on_delete=models.CASCADE, related_name="lines")
    item_type = models.CharField(max_length=20, choices=CheckoutReceiptLineType.choices)
    # Cross-service reference (a cymed Order id or a cyshop SalesOrder id)
    # — never a Django FK, cymed and cyshop are separate databases.
    external_reference = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        db_table = "platform_checkout_receipt_lines"
        ordering = ["id"]

    def __str__(self) -> str:
        return f"CheckoutReceiptLine({self.item_type}, {self.external_reference}, {self.amount})"
