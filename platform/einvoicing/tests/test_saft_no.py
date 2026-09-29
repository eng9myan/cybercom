"""Norwegian SAF-T Financial 1.40 builder tests (XSD-validated)."""
from datetime import date
from decimal import Decimal

from lxml import etree

from platform.einvoicing.periodic.saft_no import (
    NS,
    SaftAccount,
    SaftAddress,
    SaftCompany,
    SaftInput,
    SaftLine,
    SaftParty,
    SaftTax,
    SaftTransaction,
    build_saft_no,
    grouping_codes,
    schema_errors,
    standard_tax_codes,
)


def _input(**kw):
    company = SaftCompany(registration_number="999999999", name="Cycom Norge AS", contact_first_name="Ola",
                          contact_last_name="Nordmann", telephone="75757575",
                          address=SaftAddress(street="Karl Johans gate", number="1", city="Oslo", postal_code="0154"))
    sale = SaftTransaction(
        transaction_id="INV-1", date=date(2026, 3, 5), description="Invoice INV-1",
        system_entry_date=date(2026, 3, 5), voucher_type="Sales invoice",
        lines=[
            SaftLine("1500", "Customer", debit=Decimal("1250.00"), customer_id="C1"),
            SaftLine("3000", "Consulting", credit=Decimal("1000.00"),
                     tax=SaftTax("3", Decimal("25"), Decimal("1000.00"), Decimal("250.00"), debit=False)),
            SaftLine("2700", "Output VAT", credit=Decimal("250.00")),
        ])
    base = dict(
        company=company, period_start=date(2026, 1, 1), period_end=date(2026, 12, 31), currency="NOK",
        accounts=[
            SaftAccount("1500", "Accounts receivable", "balanseverdiForOmloepsmiddel", "1500",
                        Decimal("0"), Decimal("1250.00")),
            SaftAccount("2700", "Output VAT", "kortsiktigGjeld", "2700", Decimal("0"), Decimal("-250.00")),
            SaftAccount("3000", "Sales", "salgsinntekt", "3000", Decimal("0"), Decimal("-1000.00")),
        ],
        customers=[SaftParty("C1", "Kunde AS", "922222229", balance_account_id="1500",
                             opening=Decimal("0"), closing=Decimal("1250.00"))],
        suppliers=[],
        transactions=[sale], created=date(2026, 9, 29),
    )
    base.update(kw)
    return SaftInput(**base)


def test_official_code_lists_are_loaded():
    codes = grouping_codes()
    assert "1500" in codes["balanseverdiForOmloepsmiddel"]
    assert "3000" in codes["salgsinntekt"]
    assert standard_tax_codes()["3"]


def test_audit_file_is_valid_against_the_skatteetaten_xsd():
    xml = build_saft_no(_input())
    assert schema_errors(xml) == []
    root = etree.fromstring(xml.encode())
    ns = {"n": NS}
    assert root.xpath("string(//n:AuditFileVersion)", namespaces=ns) == "1.40"
    assert root.xpath("string(//n:TotalDebit)", namespaces=ns) == "1250.00"
    assert root.xpath("string(//n:TotalCredit)", namespaces=ns) == "1250.00"
    assert root.xpath("string(//n:TaxCodeDetails/n:StandardTaxCode)", namespaces=ns) == "3"
    assert root.xpath("string(//n:Account[n:AccountID='2700']/n:ClosingCreditBalance)", namespaces=ns) == "250.00"
    assert root.xpath("string(//n:TaxRegistrationNumber)", namespaces=ns) == "999999999MVA"


def test_empty_period_is_still_valid():
    assert schema_errors(build_saft_no(_input(transactions=[], customers=[]))) == []


def test_schema_check_is_real():
    xml = build_saft_no(_input())
    assert schema_errors(xml.replace("<AccountType>GL</AccountType>", "<AccountType>XX</AccountType>", 1))
