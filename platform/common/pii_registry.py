"""
PII / PHI field registry.

Encrypted fields register themselves here at class definition. The registry
drives:
  * the DPIA / data-map (what personal data we hold, where),
  * the residency data-flow lint (`H` C1 — regulated categories must not leave
    the tenant's region, incl. logs/analytics/backups),
  * DSAR export/erasure (know every column holding a subject's data).

Read it with `registered_pii_fields()`.
"""
from __future__ import annotations

from dataclasses import dataclass

# classification -> the strictest handling it implies
CLASSES = {
    "pii": "personal data (name, contact, IDs)",
    "phi": "protected health information — highest sensitivity, in-region only",
    "financial_id": "IBAN / card / financial-identity — PCI-adjacent",
    "national_id": "national ID / Iqama / passport — residency-restricted",
}


@dataclass(frozen=True)
class PiiField:
    model_label: str      # "<app_label>.<ModelName>"
    field_name: str
    classification: str
    blind_indexed: bool


_REGISTRY: dict[tuple[str, str], PiiField] = {}


def register_pii_field(model_label: str, field_name: str, classification: str,
                       blind_indexed: bool = False) -> None:
    if classification not in CLASSES:
        raise ValueError(f"unknown PII classification {classification!r}; one of {list(CLASSES)}")
    _REGISTRY[(model_label, field_name)] = PiiField(
        model_label, field_name, classification, blind_indexed
    )


def registered_pii_fields() -> list[PiiField]:
    return sorted(_REGISTRY.values(), key=lambda f: (f.model_label, f.field_name))


def is_registered(model_label: str, field_name: str) -> bool:
    return (model_label, field_name) in _REGISTRY
