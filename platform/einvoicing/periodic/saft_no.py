"""
Norway -- SAF-T Financial, schema v1.40 (Skatteetaten), built against the
official XSD vendored under schemas/no/ together with the official code
lists it depends on:

- naeringsspesifikasjon_2025-2026.csv: GroupingCategory / GroupingCode
  pairs every GL account must be mapped to (mandatory in 1.40);
- Standard_Tax_Codes.csv: the standard VAT codes each tax code maps to.

SAF-T is a periodic audit export (produced on request from the tax
authority), not a per-invoice clearance. This module is a pure builder: it
takes a fully-resolved `SaftInput` (the product layer computes balances,
transactions and tax information from its ledger) and returns the XML; it
never invents a mapping -- an unmapped account or an unclassified 0% line
is reported by the caller as missing data.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from functools import lru_cache

from lxml import etree as ET

from ..national.base import SCHEMAS_DIR, fmt, validate_against_xsd

NS = "urn:StandardAuditFile-Taxation-Financial:NO"
XSD = "no/Norwegian_SAF-T_Financial_Schema_v_1.40.xsd"


@lru_cache(maxsize=1)
def grouping_codes() -> dict[str, dict[str, str]]:
    """{GroupingCategory: {GroupingCode: English description}} from the
    official næringsspesifikasjon list."""
    out: dict[str, dict[str, str]] = {}
    with open(SCHEMAS_DIR / "no" / "naeringsspesifikasjon_2025-2026.csv", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            if row.get("GroupingCategory") and row.get("GroupingCode"):
                out.setdefault(row["GroupingCategory"], {})[row["GroupingCode"]] = (
                    row.get("CodeDescriptionENG") or row.get("CodeDescriptionNOB") or "")
    return out


@lru_cache(maxsize=1)
def standard_tax_codes() -> dict[str, str]:
    with open(SCHEMAS_DIR / "no" / "Standard_Tax_Codes.csv", encoding="utf-8-sig") as fh:
        return {r["Code"]: r.get("DescriptionENG") or r.get("DescriptionNOB") or ""
                for r in csv.DictReader(fh, delimiter=";") if r.get("Code")}


# Unambiguous mappings; a 0% line always needs an explicit code.
SALES_CODE_BY_RATE = {Decimal("25"): "3", Decimal("15"): "31", Decimal("12"): "33", Decimal("11.11"): "32"}
PURCHASE_CODE_BY_RATE = {Decimal("25"): "1", Decimal("15"): "11", Decimal("12"): "13", Decimal("11.11"): "12"}
SALES_ZERO_CODES = ("5", "51", "52", "6", "7")
PURCHASE_ZERO_CODES = ("0", "20", "85")


@dataclass
class SaftAddress:
    street: str = ""
    number: str = ""
    city: str = ""
    postal_code: str = ""
    country: str = "NO"


@dataclass
class SaftCompany:
    registration_number: str        # organisasjonsnummer, 9 digits
    name: str
    contact_first_name: str
    contact_last_name: str
    telephone: str
    address: SaftAddress = field(default_factory=SaftAddress)
    vat_registered: bool = True
    email: str = ""


@dataclass
class SaftAccount:
    account_id: str
    description: str
    grouping_category: str
    grouping_code: str
    opening: Decimal                # debit-positive
    closing: Decimal


@dataclass
class SaftParty:
    party_id: str
    name: str
    registration_number: str = ""
    address: SaftAddress | None = None
    balance_account_id: str = ""
    opening: Decimal = Decimal("0")
    closing: Decimal = Decimal("0")


@dataclass
class SaftTax:
    code: str                       # our TaxCode == the standard code
    percentage: Decimal
    base: Decimal
    amount: Decimal
    debit: bool                     # DebitTaxAmount vs CreditTaxAmount


@dataclass
class SaftLine:
    account_id: str
    description: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    customer_id: str = ""
    supplier_id: str = ""
    tax: SaftTax | None = None


@dataclass
class SaftTransaction:
    transaction_id: str
    date: date
    description: str
    system_entry_date: date
    lines: list[SaftLine]
    source_id: str = ""
    voucher_type: str = ""


@dataclass
class SaftInput:
    company: SaftCompany
    period_start: date
    period_end: date
    currency: str
    accounts: list[SaftAccount]
    customers: list[SaftParty]
    suppliers: list[SaftParty]
    transactions: list[SaftTransaction]
    software_version: str = "1.0"
    created: date | None = None


def build_saft_no(data: SaftInput) -> str:
    root = ET.Element(f"{{{NS}}}AuditFile", nsmap={None: NS})
    h = _e(root, "Header")
    _t(h, "AuditFileVersion", "1.40")
    _t(h, "AuditFileCountry", "NO")
    _t(h, "AuditFileDateCreated", (data.created or date.today()).isoformat())
    _t(h, "SoftwareCompanyName", "CyCom")
    _t(h, "SoftwareID", "CyCom ERP")
    _t(h, "SoftwareVersion", data.software_version)
    c = _e(h, "Company")
    _t(c, "RegistrationNumber", data.company.registration_number)
    _t(c, "Name", data.company.name)
    _address(c, data.company.address)
    contact = _e(c, "Contact")
    person = _e(contact, "ContactPerson")
    _t(person, "FirstName", data.company.contact_first_name)
    _t(person, "LastName", data.company.contact_last_name)
    _t(contact, "Telephone", data.company.telephone)
    if data.company.email:
        _t(contact, "Email", data.company.email)
    if data.company.vat_registered:
        tr = _e(c, "TaxRegistration")
        _t(tr, "TaxRegistrationNumber", f"{data.company.registration_number}MVA")
        _t(tr, "TaxAuthority", "Skatteetaten")
    _t(h, "DefaultCurrencyCode", data.currency.upper())
    sc = _e(h, "SelectionCriteria")
    _t(sc, "SelectionStartDate", data.period_start.isoformat())
    _t(sc, "SelectionEndDate", data.period_end.isoformat())
    _t(h, "TaxAccountingBasis", "A")

    mf = _e(root, "MasterFiles")
    gla = _e(mf, "GeneralLedgerAccounts")
    for a in data.accounts:
        acc = _e(gla, "Account")
        _t(acc, "AccountID", a.account_id)
        _t(acc, "AccountDescription", a.description[:256])
        _t(acc, "GroupingCategory", a.grouping_category)
        _t(acc, "GroupingCode", a.grouping_code)
        _t(acc, "AccountType", "GL")
        _balance(acc, a.opening, a.closing)
    for tag, id_tag, parties in (("Customers", "CustomerID", data.customers),
                                 ("Suppliers", "SupplierID", data.suppliers)):
        if not parties:
            continue
        wrap = _e(mf, tag)
        for p in parties:
            el = _e(wrap, tag[:-1])
            if p.registration_number:
                _t(el, "RegistrationNumber", p.registration_number[:35])
            _t(el, "Name", p.name[:256])
            if p.address:
                _address(el, p.address)
            _t(el, id_tag, p.party_id[:35])
            if p.balance_account_id:
                ba = _e(el, "BalanceAccount")
                _t(ba, "AccountID", p.balance_account_id)
                _balance(ba, p.opening, p.closing)

    used = {}
    for tx in data.transactions:
        for ln in tx.lines:
            if ln.tax:
                used[ln.tax.code] = ln.tax.percentage
    if used:
        tt = _e(_e(mf, "TaxTable"), "TaxTableEntry")
        _t(tt, "TaxType", "MVA")
        _t(tt, "Description", "Merverdiavgift")
        std = standard_tax_codes()
        for code, pct in sorted(used.items()):
            d = _e(tt, "TaxCodeDetails")
            _t(d, "TaxCode", code)
            _t(d, "Description", std.get(code, "")[:256])
            _t(d, "TaxPercentage", _pct(pct))
            _t(d, "Country", "NO")
            _t(d, "StandardTaxCode", code)
            _t(d, "BaseRate", "100")

    total_debit = sum((ln.debit for tx in data.transactions for ln in tx.lines), Decimal("0"))
    total_credit = sum((ln.credit for tx in data.transactions for ln in tx.lines), Decimal("0"))
    gle = _e(root, "GeneralLedgerEntries")
    _t(gle, "NumberOfEntries", str(len(data.transactions)))
    _t(gle, "TotalDebit", fmt(total_debit, 2))
    _t(gle, "TotalCredit", fmt(total_credit, 2))
    if data.transactions:
        j = _e(gle, "Journal")
        _t(j, "JournalID", "GL")
        _t(j, "Description", "General ledger")
        _t(j, "Type", "GL")
        for tx in data.transactions:
            t = _e(j, "Transaction")
            _t(t, "TransactionID", tx.transaction_id[:70])
            _t(t, "Period", str(tx.date.month))
            _t(t, "PeriodYear", str(tx.date.year))
            _t(t, "TransactionDate", tx.date.isoformat())
            if tx.source_id:
                _t(t, "SourceID", tx.source_id[:35])
            if tx.voucher_type:
                _t(t, "VoucherType", tx.voucher_type[:70])
            _t(t, "Description", (tx.description or "-")[:256])
            _t(t, "SystemEntryDate", tx.system_entry_date.isoformat())
            _t(t, "GLPostingDate", tx.date.isoformat())
            for n, ln in enumerate(tx.lines, start=1):
                le = _e(t, "Line")
                _t(le, "RecordID", str(n))
                _t(le, "AccountID", ln.account_id)
                if ln.customer_id:
                    _t(le, "CustomerID", ln.customer_id[:35])
                if ln.supplier_id:
                    _t(le, "SupplierID", ln.supplier_id[:35])
                _t(le, "Description", (ln.description or tx.description or "-")[:256])
                amt = _e(le, "DebitAmount" if ln.debit else "CreditAmount")
                _t(amt, "Amount", fmt(ln.debit or ln.credit, 2))
                if ln.tax:
                    ti = _e(le, "TaxInformation")
                    _t(ti, "TaxType", "MVA")
                    _t(ti, "TaxCode", ln.tax.code)
                    _t(ti, "TaxPercentage", _pct(ln.tax.percentage))
                    _t(ti, "TaxBase", fmt(ln.tax.base, 2))
                    ta = _e(ti, "DebitTaxAmount" if ln.tax.debit else "CreditTaxAmount")
                    _t(ta, "Amount", fmt(ln.tax.amount, 2))

    return ET.tostring(root, encoding="UTF-8", xml_declaration=True).decode("utf-8")


def schema_errors(xml: str) -> list[str]:
    return validate_against_xsd(xml, XSD)


def _e(parent, tag):
    return ET.SubElement(parent, f"{{{NS}}}{tag}")


def _t(parent, tag, text):
    el = _e(parent, tag)
    el.text = str(text)
    return el


def _address(parent, a: SaftAddress):
    addr = _e(parent, "Address")
    if a.street:
        _t(addr, "StreetName", a.street[:256])
    if a.number:
        _t(addr, "Number", a.number[:70])
    if a.city:
        _t(addr, "City", a.city[:256])
    if a.postal_code:
        _t(addr, "PostalCode", a.postal_code[:70])
    if a.country:
        _t(addr, "Country", a.country.upper())


def _balance(parent, opening: Decimal, closing: Decimal):
    _t(parent, "OpeningDebitBalance" if opening >= 0 else "OpeningCreditBalance", fmt(abs(opening), 2))
    _t(parent, "ClosingDebitBalance" if closing >= 0 else "ClosingCreditBalance", fmt(abs(closing), 2))


def _pct(p: Decimal) -> str:
    d = Decimal(str(p)).normalize()
    return str(int(d)) if d == d.to_integral_value() else format(d, "f")
