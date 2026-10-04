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
from .br_nfe import BrNfe
from .eg_eta import EgEta
from .es_sii import EsSii
from .in_gst import InGst
from .it_fatturapa import ItFatturaPA
from .mx_cfdi import MxCfdi
from .pl_ksef import PlKsef

FORMATS: dict[str, NationalFormat] = {
    f.mode: f for f in (
        ItFatturaPA(),
        PlKsef(),
        MxCfdi(),
        BrNfe(),
        InGst(),
        EsSii(),
        EgEta(),
    )
}

COUNTRY_MODES: dict[str, str] = {c: f.mode for f in FORMATS.values() for c in f.countries}


def get_format(mode: str) -> NationalFormat | None:
    return FORMATS.get(mode)
