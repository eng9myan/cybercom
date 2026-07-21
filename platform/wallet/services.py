from decimal import Decimal

from django.db import transaction

from platform.cyidentity.models import PersonIdentity
from platform.tenant.permissions import IsPlatformAdmin
from platform.wallet.models import WalletAccount, WalletEntryType, WalletLedgerEntry


class InsufficientFundsError(Exception):
    pass


def resolve_person_from_request(request, requested_person_id=None) -> "PersonIdentity | None":
    """platform_admin (service-to-service, e.g. a checkout flow acting on
    a customer's behalf) may act on any person_id supplied; everyone else
    can only act on their own CyID (the person_id claim on their own
    token, per Phase 2's opt-in claim mapper). Shared by wallet views and
    the cross-network checkout view (Phase 8) — same auth-resolution
    logic, not duplicated."""
    claims = getattr(request, "auth_claims", {}) or {}
    roles = set(claims.get("realm_access", {}).get("roles", []) or [])
    is_admin = bool(roles & IsPlatformAdmin.ADMIN_ROLES)

    if is_admin and requested_person_id:
        person_id = requested_person_id
    else:
        person_id = claims.get("person_id")
    if not person_id:
        return None
    return PersonIdentity.objects.filter(id=person_id).first()


class WalletService:
    @transaction.atomic
    def top_up(
        self, person: PersonIdentity, currency: str, amount: Decimal, *, reference: str = "", created_by: str = ""
    ) -> WalletLedgerEntry:
        if amount <= 0:
            raise ValueError("top_up amount must be positive")
        wallet, _ = WalletAccount.objects.select_for_update().get_or_create(
            person=person, currency=currency
        )
        wallet.balance = wallet.balance + amount
        wallet.save(update_fields=["balance", "updated_at"])
        return WalletLedgerEntry.objects.create(
            wallet=wallet,
            entry_type=WalletEntryType.TOPUP,
            amount=amount,
            balance_after=wallet.balance,
            reference=reference,
            created_by=created_by,
        )

    @transaction.atomic
    def debit(
        self, person: PersonIdentity, currency: str, amount: Decimal, *, reference: str = "", created_by: str = ""
    ) -> WalletLedgerEntry:
        if amount <= 0:
            raise ValueError("debit amount must be positive")
        try:
            wallet = WalletAccount.objects.select_for_update().get(person=person, currency=currency)
        except WalletAccount.DoesNotExist as exc:
            raise InsufficientFundsError(
                f"No {currency} wallet exists for this person."
            ) from exc
        if wallet.balance < amount:
            raise InsufficientFundsError(
                f"Insufficient {currency} balance: have {wallet.balance}, need {amount}."
            )
        wallet.balance = wallet.balance - amount
        wallet.save(update_fields=["balance", "updated_at"])
        return WalletLedgerEntry.objects.create(
            wallet=wallet,
            entry_type=WalletEntryType.DEBIT,
            amount=amount,
            balance_after=wallet.balance,
            reference=reference,
            created_by=created_by,
        )

    @staticmethod
    def get_balance(person: PersonIdentity, currency: str) -> Decimal:
        wallet = WalletAccount.objects.filter(person=person, currency=currency).first()
        return wallet.balance if wallet else Decimal("0")
