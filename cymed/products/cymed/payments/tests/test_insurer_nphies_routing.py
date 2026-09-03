from __future__ import annotations

import pytest


def test_known_saudi_insurer_code_routes_to_nphies():
    from products.cymed.payments.insurers import get_insurer
    from products.cymed.payments.insurers.nphies import NphiesInsurer

    for code in ("BUPA", "TAWUNIYA", "MEDGULF", "MALATH", "WALAA", "ARABIA", "NPHIES"):
        ins = get_insurer(code, country="SA")
        assert isinstance(ins, NphiesInsurer), f"{code} should route to NPHIES"
        assert ins.country == "SA"
        assert ins.code == "NPHIES"


def test_case_insensitive_code_lookup():
    from products.cymed.payments.insurers import get_insurer
    from products.cymed.payments.insurers.nphies import NphiesInsurer

    ins = get_insurer("bupa", country="SA")
    assert isinstance(ins, NphiesInsurer)


def test_unknown_saudi_insurer_falls_back_to_default_sa_nphies():
    from products.cymed.payments.insurers import get_insurer
    from products.cymed.payments.insurers.nphies import NphiesInsurer

    ins = get_insurer("SOME_UNLISTED_SA_INSURER", country="SA")
    # The SA default alias points at the NPHIES adapter.
    assert isinstance(ins, NphiesInsurer)


def test_unknown_jordan_insurer_falls_back_to_manual():
    from products.cymed.payments.insurers import get_insurer
    from products.cymed.payments.insurers.manual import ManualInsurer

    ins = get_insurer("UNKNOWN_JO_INSURER", country="JO")
    assert isinstance(ins, ManualInsurer)
    assert ins.code == "MANUAL"


def test_unknown_country_falls_back_to_manual():
    from products.cymed.payments.insurers import get_insurer
    from products.cymed.payments.insurers.manual import ManualInsurer

    # Country with no default alias registered → last-resort MANUAL adapter.
    ins = get_insurer("UNKNOWN_INSURER", country="XX")
    assert isinstance(ins, ManualInsurer)


def test_empty_insurer_code_falls_back_via_country():
    from products.cymed.payments.insurers import get_insurer
    from products.cymed.payments.insurers.manual import ManualInsurer
    from products.cymed.payments.insurers.nphies import NphiesInsurer

    assert isinstance(get_insurer("", country="SA"), NphiesInsurer)
    assert isinstance(get_insurer("", country="JO"), ManualInsurer)
