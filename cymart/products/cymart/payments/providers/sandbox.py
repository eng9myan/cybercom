"""
Deterministic sandbox provider — not a mock used only in tests, but a
real, complete implementation of PaymentProvider that PaymentService can
run against in dev/CI without any external gateway. Behavior is
deterministic based on the payment_method_token, mirroring how real
gateways' test modes work (e.g. Stripe's test card numbers that trigger
specific declines) — "decline_*" tokens fail, everything else succeeds.
"""

import uuid
from decimal import Decimal

from .base import PaymentProvider, ProviderResult


class SandboxPaymentProvider(PaymentProvider):
    def authorize(self, amount: Decimal, currency: str, payment_method_token: str) -> ProviderResult:
        if payment_method_token.startswith("decline_"):
            return ProviderResult(
                success=False,
                provider_reference="",
                amount=amount,
                failure_reason="Sandbox: card declined (token requested a decline).",
            )
        return ProviderResult(
            success=True, provider_reference=f"sandbox_auth_{uuid.uuid4().hex[:16]}", amount=amount
        )

    def capture(self, provider_reference: str, amount: Decimal) -> ProviderResult:
        if not provider_reference:
            return ProviderResult(
                success=False, provider_reference="", amount=amount,
                failure_reason="Sandbox: no authorization reference to capture against.",
            )
        return ProviderResult(success=True, provider_reference=provider_reference, amount=amount)

    def void(self, provider_reference: str) -> ProviderResult:
        if not provider_reference:
            return ProviderResult(
                success=False, provider_reference="", amount=Decimal("0"),
                failure_reason="Sandbox: no authorization reference to void.",
            )
        return ProviderResult(success=True, provider_reference=provider_reference, amount=Decimal("0"))

    def refund(self, provider_reference: str, amount: Decimal) -> ProviderResult:
        if not provider_reference:
            return ProviderResult(
                success=False, provider_reference="", amount=amount,
                failure_reason="Sandbox: no capture reference to refund against.",
            )
        return ProviderResult(success=True, provider_reference=provider_reference, amount=amount)
