"""Base contract every payment gateway must implement.

The `charge` and `refund` signatures accept two additive keyword-only
parameters — `idempotency_key` and `tenant_id` — with `None` defaults so
existing callers keep working. Concrete gateways may use them (e.g.
HyperPay stamps `merchantTransactionId` and a customParameters tenant tag
so webhooks can be routed back).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class ChargeResult:
    success: bool
    gateway_reference: str
    status: str                         # 'succeeded' | 'pending' | 'failed'
    raw: dict[str, Any] = field(default_factory=dict)
    error_message: str = ""


@dataclass
class RefundResult:
    success: bool
    gateway_reference: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class WebhookEvent:
    event_type: str                     # 'payment.succeeded', 'payment.failed', ...
    gateway_reference: str
    raw: dict[str, Any] = field(default_factory=dict)


class BaseGateway(ABC):
    name: str
    supports: list[str]                 # ['card', 'apple_pay', ...]

    @abstractmethod
    def tokenize(self, payload: dict) -> str: ...

    @abstractmethod
    def charge(
        self,
        token: str,
        amount: Decimal,
        currency: str,
        metadata: dict,
        *,
        idempotency_key: str | None = None,
        tenant_id: str | None = None,
    ) -> ChargeResult: ...

    @abstractmethod
    def refund(
        self,
        gateway_ref: str,
        amount: Decimal | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> RefundResult: ...

    @abstractmethod
    def webhook_verify(self, headers: dict, body: bytes) -> bool: ...

    @abstractmethod
    def webhook_parse(self, body: bytes) -> WebhookEvent: ...
