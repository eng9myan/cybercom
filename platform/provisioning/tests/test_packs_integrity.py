"""
Structural validation of every catalog pack on disk.

Packs are hand/script authored JSON, so a typo doesn't fail until a tenant
provisions against it -- by which point it's a broken onboarding, not a
build error. These tests fail fast instead.

They deliberately check *internal consistency* (a pack referencing a
department that exists, approval tiers that don't leave a gap, accounts
hanging off a real parent) rather than just "is it valid JSON".
"""

import json
from pathlib import Path

import pytest

PACKS = Path(__file__).resolve().parent.parent / "packs"
INDUSTRIES = sorted((PACKS / "industries").glob("*.json"))
COUNTRIES = sorted((PACKS / "countries").glob("*.json"))
DEPARTMENTS = sorted((PACKS / "departments").glob("*.json"))

DEPARTMENT_KEYS = {p.stem for p in DEPARTMENTS}
ACCOUNT_TYPES = {"asset", "liability", "equity", "income", "expense"}


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _ids(paths):
    return [p.stem for p in paths]


# ── industries ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("path", INDUSTRIES, ids=_ids(INDUSTRIES))
def test_industry_pack_has_required_shape(path):
    pack = _load(path)
    for field in ("key", "name", "version", "description", "department_pack_keys"):
        assert pack.get(field), f"{path.name}: missing '{field}'"
    assert pack["key"] == path.stem, f"{path.name}: key must match filename"


@pytest.mark.parametrize("path", INDUSTRIES, ids=_ids(INDUSTRIES))
def test_industry_references_only_real_department_packs(path):
    pack = _load(path)
    unknown = set(pack["department_pack_keys"]) - DEPARTMENT_KEYS
    assert not unknown, f"{path.name}: references non-existent departments {unknown}"


@pytest.mark.parametrize("path", INDUSTRIES, ids=_ids(INDUSTRIES))
def test_industry_approval_tiers_are_ordered_and_gapless(path):
    """A tier whose min doesn't continue the previous tier's max leaves an
    amount band nobody is authorised to approve -- the document would hit
    no tier at all at runtime."""
    for matrix in _load(path).get("approval_matrix", []):
        tiers = matrix["tiers"]
        assert tiers, f"{path.name}: '{matrix['document_type']}' has no tiers"
        assert tiers[0]["min"] == 0, f"{path.name}: '{matrix['document_type']}' must start at 0"
        for prev, nxt in zip(tiers, tiers[1:]):
            assert prev["max"] is not None, (
                f"{path.name}: '{matrix['document_type']}' has an open-ended tier before the last"
            )
            assert nxt["min"] == prev["max"], (
                f"{path.name}: '{matrix['document_type']}' gap/overlap "
                f"between {prev['max']} and {nxt['min']}"
            )
        assert tiers[-1]["max"] is None, (
            f"{path.name}: '{matrix['document_type']}' last tier must be open-ended "
            f"or large amounts match no tier"
        )
        for t in tiers:
            assert t.get("role"), f"{path.name}: tier without a role"


@pytest.mark.parametrize("path", INDUSTRIES, ids=_ids(INDUSTRIES))
def test_industry_extra_accounts_are_well_formed(path):
    for acct in _load(path).get("accounting_mappings", {}).get("extra_accounts", []):
        assert acct["account_type"] in ACCOUNT_TYPES, f"{path.name}: bad account_type {acct}"
        assert acct["code"].isdigit(), f"{path.name}: non-numeric account code {acct['code']}"
        assert acct.get("name"), f"{path.name}: account {acct['code']} has no name"


def test_industry_account_codes_are_unique_within_each_pack():
    for path in INDUSTRIES:
        codes = [a["code"] for a in _load(path).get("accounting_mappings", {}).get("extra_accounts", [])]
        dupes = {c for c in codes if codes.count(c) > 1}
        assert not dupes, f"{path.name}: duplicate account codes {dupes}"


@pytest.mark.parametrize("path", INDUSTRIES, ids=_ids(INDUSTRIES))
def test_industry_roles_referenced_by_approvals_are_defined_or_global(path):
    """Every approval role must be one a tenant actually gets. Provisioning
    (_generate_roles) composes roles from exactly two places -- the industry
    pack's own default_config.roles and the roles of the department packs it
    references. There is no implicit global role set, so anything else in an
    approval tier points at a role that is never created and leaves that
    document permanently unapprovable."""
    pack = _load(path)
    declared = {r["name"] for r in pack.get("default_config", {}).get("roles", [])}
    for dept_key in pack.get("department_pack_keys", []):
        dept = _load(PACKS / "departments" / f"{dept_key}.json")
        declared |= {r["name"] for r in dept.get("roles", [])}
    used = {t["role"] for m in pack.get("approval_matrix", []) for t in m["tiers"]}
    unknown = used - declared
    assert not unknown, (
        f"{path.name}: approval roles not created by this pack or its "
        f"department packs: {unknown}"
    )


@pytest.mark.parametrize("path", INDUSTRIES, ids=_ids(INDUSTRIES))
def test_industry_has_usable_ai_knowledge(path):
    ai = _load(path).get("ai_knowledge", {})
    assert ai.get("domain_notes"), f"{path.name}: no domain notes"
    assert len(ai.get("starter_prompts", [])) >= 3, f"{path.name}: needs >=3 starter prompts"


def test_industry_keys_are_globally_unique():
    keys = [_load(p)["key"] for p in INDUSTRIES]
    dupes = {k for k in keys if keys.count(k) > 1}
    assert not dupes, f"duplicate industry keys: {dupes}"


# ── countries ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("path", COUNTRIES, ids=_ids(COUNTRIES))
def test_country_pack_has_required_shape(path):
    pack = _load(path)
    for field in ("code", "name", "currency", "languages", "default_locale", "coa_template"):
        assert pack.get(field), f"{path.name}: missing '{field}'"
    assert pack["code"] == path.stem, f"{path.name}: code must match filename"
    assert len(pack["code"]) == 2, f"{path.name}: code must be ISO-3166 alpha-2"
    assert pack["default_locale"] in pack["languages"], (
        f"{path.name}: default_locale '{pack['default_locale']}' not in languages"
    )
    assert 1 <= pack.get("fiscal_year_start_month", 1) <= 12


@pytest.mark.parametrize("path", COUNTRIES, ids=_ids(COUNTRIES))
def test_country_chart_of_accounts_parents_resolve(path):
    """A parent code that isn't itself in the chart produces an orphan
    account at provisioning time."""
    coa = _load(path)["coa_template"]
    codes = {a["code"] for a in coa}
    for acct in coa:
        assert acct["account_type"] in ACCOUNT_TYPES, f"{path.name}: bad type on {acct['code']}"
        parent = acct.get("parent")
        if parent is not None:
            assert parent in codes, f"{path.name}: {acct['code']} has unknown parent {parent}"


@pytest.mark.parametrize("path", COUNTRIES, ids=_ids(COUNTRIES))
def test_country_tax_and_payroll_rates_are_flagged_unverified(path):
    """Published headline rates are a starting point, not advice. Every pack
    must carry the flag so nobody ships payroll without local sign-off."""
    pack = _load(path)
    if pack["code"] == "JO":
        return  # the original hand-authored reference pack
    assert pack["tax_config"].get("rates_verified") is False, f"{path.name}: tax rates not flagged"
    assert pack["payroll_config"].get("rates_verified") is False, f"{path.name}: payroll not flagged"


@pytest.mark.parametrize("path", COUNTRIES, ids=_ids(COUNTRIES))
def test_country_income_tax_brackets_ascend_and_end_open(path):
    brackets = _load(path)["payroll_config"].get("income_tax_brackets", [])
    if not brackets:
        return  # no personal income tax (several GCC states)
    bounds = [b["up_to"] for b in brackets]
    assert bounds[-1] is None, f"{path.name}: top bracket must be open-ended"
    finite = [b for b in bounds[:-1]]
    assert finite == sorted(finite), f"{path.name}: brackets out of order"
    assert all(b is not None for b in finite), f"{path.name}: only the last bracket may be open"


@pytest.mark.parametrize("path", COUNTRIES, ids=_ids(COUNTRIES))
def test_country_einvoicing_declares_a_known_status(path):
    ei = _load(path).get("einvoicing", {})
    assert ei.get("system"), f"{path.name}: einvoicing.system missing"
    assert ei.get("status") in {"ready", "planned", "none", "not_implemented"}, (
        f"{path.name}: unknown einvoicing status {ei.get('status')!r}"
    )


def test_peppol_country_packs_agree_with_the_engine_routing():
    """A pack claiming Peppol must actually route to the Peppol mode, or
    onboarding promises an e-invoicing capability the engine won't deliver."""
    from platform.einvoicing.engine import mode_for_country

    for path in COUNTRIES:
        pack = _load(path)
        if pack.get("einvoicing", {}).get("system") == "peppol":
            assert mode_for_country(pack["code"]) == "eu_peppol", (
                f"{path.name}: pack says peppol but engine routes "
                f"{mode_for_country(pack['code'])!r}"
            )


def test_catalog_is_actually_broad():
    """Guards the breadth claim: this is the number quoted against
    competitors, so it shouldn't silently regress."""
    assert len(INDUSTRIES) >= 45, f"only {len(INDUSTRIES)} industry packs"
    assert len(COUNTRIES) >= 10, f"only {len(COUNTRIES)} country packs"
