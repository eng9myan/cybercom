"""Base contract every insurer adapter must implement."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
from uuid import UUID


@dataclass
class EligibilityResult:
    covered: bool
    co_pay_amount: Decimal | None = None
    co_pay_percent: Decimal | None = None
    requires_preauth: bool = False
    patient_responsibility: Decimal | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class PreAuthResult:
    status: str                        # 'pending' | 'approved' | 'denied' | 'expired'
    reference_number: str = ""
    approved_amount: Decimal | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClaimResult:
    accepted: bool
    reference_number: str = ""
    denial_reason: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


class BaseInsurer(ABC):
    code: str                          # e.g. 'NPHIES', 'JOFOTARA', 'DIRECT_BUPA'
    country: str                       # 'SA' | 'JO'

    @abstractmethod
    def eligibility(self, policy, service_code: str,
                    provider_tenant_id: UUID | None = None) -> EligibilityResult: ...

    @abstractmethod
    def preauth_submit(self, policy, service_code: str,
                       justification: str, provider_tenant_id: UUID) -> PreAuthResult: ...

    @abstractmethod
    def preauth_status(self, reference: str) -> PreAuthResult: ...

    @abstractmethod
    def claim_submit(self, bill) -> ClaimResult: ...
