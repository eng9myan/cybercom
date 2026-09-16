"""
Provider-agnostic payment gateway seam.

CyEd has no live merchant account yet, so no real gateway can be integrated
today. What *can* be built correctly today is the boundary: every operation the
rest of the system performs against a gateway goes through `PaymentProvider`,
so dropping in Stripe / eWAY / Pin Payments later is a new subclass and an env
var, not a redesign.

Two providers ship working:

  manual — records offline money (BPAY, bank transfer, cash, EFTPOS terminal)
           against a PaymentIntent. This is not a stub: it is how most
           Australian schools actually receive fee payments today, and it gives
           the finance office a real, reconciled, refundable ledger entry.
  mock   — deterministic provider for tests and local development. Can be made
           to fail on demand so failure paths are exercised.

Anything else fails loudly. `UnconfiguredProvider` exists specifically so that a
deployment which sets CYED_PAYMENT_PROVIDER=stripe without credentials raises
on the first operation instead of quietly reporting success and losing money.

NO CARD DATA passes through this module. A real provider implementation must
take an opaque client-side token, never a PAN.
"""

import hashlib
import hmac
import os
import uuid
from dataclasses import dataclass, field
from decimal import Decimal

WEBHOOK_SECRET_ENV = "CYED_PAYMENT_WEBHOOK_SECRET"
PROVIDER_ENV = "CYED_PAYMENT_PROVIDER"
DEFAULT_PROVIDER = "manual"


class PaymentProviderError(Exception):
    """Base class for gateway failures."""


class ProviderNotConfigured(PaymentProviderError):
    """
    The requested provider is unknown, or is known but has no credentials.

    Never caught-and-ignored: a payment system that degrades to "success" when
    it cannot reach the gateway is worse than one that is down.
    """


@dataclass
class ProviderResult:
    """Outcome of a single gateway operation."""

    ok: bool
    status: str = "pending"  # pending | succeeded | failed
    reference: str = ""
    failure_reason: str = ""
    raw: dict = field(default_factory=dict)


class PaymentProvider:
    """Interface every gateway adapter implements."""

    name = ""
    # Header the provider signs its webhooks with. Stripe uses Stripe-Signature,
    # eWAY uses its own; overriding this is part of writing an adapter.
    signature_header = "HTTP_X_CYED_SIGNATURE"

    # ── money movement ───────────────────────────────────────────────────────
    def authorize(self, intent) -> ProviderResult:
        """Create/authorise the charge at the gateway. Money has not moved yet."""
        raise NotImplementedError

    def capture(self, intent, amount: Decimal) -> ProviderResult:
        """Take the authorised money. After this the funds are ours."""
        raise NotImplementedError

    def refund(self, intent, amount: Decimal, reason: str = "") -> ProviderResult:
        """Return `amount` of an already-captured intent."""
        raise NotImplementedError

    # ── inbound callbacks ────────────────────────────────────────────────────
    def webhook_secret(self) -> str:
        """
        Shared secret for webhook signatures. Environment only — never a
        settings literal, never the DB, never a request parameter.
        """
        secret = os.environ.get(WEBHOOK_SECRET_ENV, "")
        if not secret:
            raise ProviderNotConfigured(
                f"{WEBHOOK_SECRET_ENV} is not set; refusing to accept unauthenticated "
                f"{self.name or 'payment'} webhooks."
            )
        return secret

    def verify_webhook(self, raw_body: bytes, signature: str) -> bool:
        """
        HMAC-SHA256 over the *raw* request body, compared in constant time.

        The raw bytes matter: re-serialising parsed JSON changes key order and
        whitespace and would break every legitimate signature, so callers must
        hand this the untouched body.
        """
        if not signature:
            return False
        expected = hmac.new(
            self.webhook_secret().encode("utf-8"), raw_body, hashlib.sha256
        ).hexdigest()
        # Providers commonly prefix the scheme, e.g. "sha256=abc123".
        candidate = signature.split("=", 1)[1].strip() if "=" in signature else signature.strip()
        return hmac.compare_digest(expected, candidate.lower())

    def sign(self, raw_body: bytes) -> str:
        """Produce the signature this provider would send. Used by tests/tools."""
        return hmac.new(
            self.webhook_secret().encode("utf-8"), raw_body, hashlib.sha256
        ).hexdigest()


class ManualProvider(PaymentProvider):
    """
    Offline payments: BPAY, bank transfer, cash at the office, EFTPOS terminal.

    `authorize` opens the intent as *pending* — issuing a BPAY reference to a
    parent does not mean the money arrived. `capture` is the finance officer
    asserting that it did, which is the moment the ledger is credited.
    """

    name = "manual"

    def authorize(self, intent) -> ProviderResult:
        ref = f"MANUAL-{uuid.uuid4().hex[:12].upper()}"
        return ProviderResult(ok=True, status="pending", reference=ref, raw={"mode": "offline"})

    def capture(self, intent, amount: Decimal) -> ProviderResult:
        return ProviderResult(
            ok=True,
            status="succeeded",
            reference=intent.provider_reference or f"MANUAL-{uuid.uuid4().hex[:12].upper()}",
            raw={"captured": str(amount)},
        )

    def refund(self, intent, amount: Decimal, reason: str = "") -> ProviderResult:
        # The actual money goes back by bank transfer; this records that it did.
        return ProviderResult(
            ok=True,
            status="succeeded",
            reference=f"MANUALRF-{uuid.uuid4().hex[:12].upper()}",
            raw={"refunded": str(amount), "reason": reason},
        )


class MockProvider(PaymentProvider):
    """
    Deterministic test double. Set CYED_PAYMENT_MOCK_FAIL=1 to make every
    operation fail, so failure handling is exercised rather than assumed.
    """

    name = "mock"

    def _failing(self) -> bool:
        return os.environ.get("CYED_PAYMENT_MOCK_FAIL") == "1"

    def authorize(self, intent) -> ProviderResult:
        if self._failing():
            return ProviderResult(ok=False, status="failed", failure_reason="mock_declined")
        return ProviderResult(ok=True, status="pending", reference=f"mock_pi_{uuid.uuid4().hex[:16]}")

    def capture(self, intent, amount: Decimal) -> ProviderResult:
        if self._failing():
            return ProviderResult(ok=False, status="failed", failure_reason="mock_capture_declined")
        return ProviderResult(
            ok=True, status="succeeded",
            reference=intent.provider_reference or f"mock_pi_{uuid.uuid4().hex[:16]}",
        )

    def refund(self, intent, amount: Decimal, reason: str = "") -> ProviderResult:
        if self._failing():
            return ProviderResult(ok=False, status="failed", failure_reason="mock_refund_declined")
        return ProviderResult(ok=True, status="succeeded", reference=f"mock_re_{uuid.uuid4().hex[:16]}")


class UnconfiguredProvider(PaymentProvider):
    """
    Placeholder for a real gateway whose adapter/credentials are not present.

    Every operation raises. This is the whole point: a school that flips
    CYED_PAYMENT_PROVIDER to "stripe" before the integration exists gets a loud
    500 on the first charge attempt, not a silent stream of intents marked
    succeeded while no money is collected.
    """

    def __init__(self, name: str):
        self.name = name

    def _fail(self):
        raise ProviderNotConfigured(
            f"Payment provider '{self.name}' has no adapter or credentials configured. "
            f"Set {PROVIDER_ENV} to a configured provider ({', '.join(sorted(_REGISTRY))}) "
            f"or implement products.cyed.payments.providers.{self.name.title()}Provider."
        )

    def authorize(self, intent) -> ProviderResult:
        self._fail()

    def capture(self, intent, amount: Decimal) -> ProviderResult:
        self._fail()

    def refund(self, intent, amount: Decimal, reason: str = "") -> ProviderResult:
        self._fail()

    def verify_webhook(self, raw_body: bytes, signature: str) -> bool:
        self._fail()


# Adapter registry. A real integration registers here and needs no other change
# anywhere in the codebase.
_REGISTRY: dict[str, type[PaymentProvider]] = {
    ManualProvider.name: ManualProvider,
    MockProvider.name: MockProvider,
}

# Gateways we know about but have not implemented. Named explicitly so the error
# message can say "not implemented yet" rather than "unknown provider".
_KNOWN_UNIMPLEMENTED = {"stripe", "eway", "pin", "braintree", "adyen", "securepay"}


def configured_provider_name() -> str:
    return os.environ.get(PROVIDER_ENV, DEFAULT_PROVIDER).strip().lower()


def get_provider(name: str | None = None) -> PaymentProvider:
    """
    Resolve a provider adapter by name, defaulting to the env-configured one.

    Raises ProviderNotConfigured for anything unknown or unimplemented — there
    is no fallback, because falling back silently is how money goes missing.
    """
    key = (name or configured_provider_name() or "").strip().lower()
    if not key:
        raise ProviderNotConfigured(f"{PROVIDER_ENV} is empty and no provider was requested.")
    if key in _REGISTRY:
        return _REGISTRY[key]()
    if key in _KNOWN_UNIMPLEMENTED:
        return UnconfiguredProvider(key)
    raise ProviderNotConfigured(
        f"Unknown payment provider '{key}'. Configured providers: {', '.join(sorted(_REGISTRY))}."
    )


def available_providers() -> list[str]:
    return sorted(_REGISTRY)
