# -*- coding: utf-8 -*-


class PeppolUblPlugin:
    """Peppol BIS Billing 3.0 UBL XML E-Invoicing Formatter for global B2B operations."""

    @staticmethod
    def generate_peppol_ubl(invoice_data: dict) -> str:
        """Generates standard compliant UBL Invoice markup."""
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:poacc:trns:invoice:3</cbc:CustomizationID>
    <cbc:ProfileID>urn:fdc:peppol.eu:poacc:bis:billing:3@gb</cbc:ProfileID>
    <cbc:ID>{invoice_data.get("number")}</cbc:ID>
    <cbc:IssueDate>{invoice_data.get("date")}</cbc:IssueDate>
    <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>USD</cbc:DocumentCurrencyCode>
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyName>
                <cbc:Name>{invoice_data.get("seller_name")}</cbc:Name>
            </cac:PartyName>
        </cac:Party>
    </cac:AccountingSupplierParty>
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyName>
                <cbc:Name>{invoice_data.get("buyer_name")}</cbc:Name>
            </cac:PartyName>
        </cac:Party>
    </cac:AccountingCustomerParty>
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="USD">{invoice_data.get("tax_amount")}</cbc:TaxAmount>
    </cac:TaxTotal>
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="USD">{invoice_data.get("gross_amount")}</cbc:LineExtensionAmount>
        <cbc:TaxExclusiveAmount currencyID="USD">{invoice_data.get("tax_amount")}</cbc:TaxExclusiveAmount>
        <cbc:PayableAmount currencyID="USD">{invoice_data.get("net_amount")}</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
</Invoice>
"""
        return xml
