"""Insurer registry — resolve insurer_code to concrete adapter."""
from .base import BaseInsurer
from .manual import ManualInsurer
from .nphies import NphiesInsurer


_registry: dict[str, BaseInsurer] = {}


def register(ins: BaseInsurer, aliases: list[str] | None = None):
    _registry[ins.code] = ins
    for a in aliases or []:
        _registry[a] = ins


def get_insurer(code: str, country: str = "SA") -> BaseInsurer:
    code = (code or "").upper()
    if code in _registry:
        return _registry[code]
    # Country fallback
    default_key = f"_default_{country.lower()}"
    if default_key in _registry:
        return _registry[default_key]
    return _registry["MANUAL"]


# Register default set. NphiesInsurer routes for BUPA/Tawuniya/MedGulf via clearing house.
nphies = NphiesInsurer()
register(nphies, aliases=["BUPA", "TAWUNIYA", "MEDGULF", "MALATH", "WALAA",
                          "ARABIA", "_default_sa"])
register(ManualInsurer(), aliases=["_default_jo"])
