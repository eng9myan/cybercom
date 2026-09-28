"""National e-invoicing formats (see base.py for the shared contract)."""
from __future__ import annotations

from .base import (  # noqa: F401
    DocInput,
    EInvoiceDataMissing,
    FieldSpec,
    LineInput,
    NationalFormat,
    PartyInput,
    TransportNotConfigured,
)
from .it_fatturapa import ItFatturaPA

FORMATS: dict[str, NationalFormat] = {
    f.mode: f for f in (
        ItFatturaPA(),
    )
}

COUNTRY_MODES: dict[str, str] = {c: f.mode for f in FORMATS.values() for c in f.countries}


def get_format(mode: str) -> NationalFormat | None:
    return FORMATS.get(mode)
