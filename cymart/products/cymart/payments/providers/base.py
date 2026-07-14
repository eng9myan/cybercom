"""
Payment provider abstraction (master spec section 17). A real gateway
adapter (Stripe, PayTabs, etc.) implements this same interface — no
credentials for any real gateway exist in this environment, so only the
interface + a deterministic sandbox implementation exist here. Swapping
in a real provider later means implementing this interface, not changing
any calling code in PaymentService.
"""

import abc
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ProviderResult:
    success: bool
    provider_reference: str
    amount: Decimal
    failure_reason: str = ""


class PaymentProvider(abc.ABC):
    @abc.abstractmethod
    def authorize(self, amount: Decimal, currency: str, payment_method_token: str) -> ProviderResult:
        """Places a hold on funds without capturing them."""

    @abc.abstractmethod
    def capture(self, provider_reference: str, amount: Decimal) -> ProviderResult:
        """Captures a previously authorized amount (full or partial)."""

    @abc.abstractmethod
    def void(self, provider_reference: str) -> ProviderResult:
        """Releases an authorization hold without capturing anything."""

    @abc.abstractmethod
    def refund(self, provider_reference: str, amount: Decimal) -> ProviderResult:
        """Refunds a previously captured amount (full or partial)."""
