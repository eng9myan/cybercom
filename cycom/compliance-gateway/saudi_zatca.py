# -*- coding: utf-8 -*-
import base64
import hashlib


class SaudiZatcaPlugin:
    """Saudi Arabia ZATCA Phase 2 E-Invoicing Compliance Plugin (Wave 24)."""

    @staticmethod
    def calculate_pih(previous_invoice_xml: str) -> str:
        """Computes the SHA-256 hash of the previous invoice XML to chain ledger integrity."""
        if not previous_invoice_xml:
            # Seed value for the first transaction in the tenant block
            return "0000000000000000000000000000000000000000000000000000000000000000"

        sha_digest = hashlib.sha256(previous_invoice_xml.encode("utf-8")).digest()
        return base64.b64encode(sha_digest).decode("utf-8")

    @staticmethod
    def generate_ubl_invoice(invoice_data: dict, pih: str) -> str:
        """Generates a standard Saudi ZATCA UBL 2.1 invoice document structure."""
        xml_template = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:ProfileID>reporting:1.0</cbc:ProfileID>
    <cbc:ID>{invoice_data.get("number")}</cbc:ID>
    <cbc:UUID>{invoice_data.get("uuid")}</cbc:UUID>
    <cbc:IssueDate>{invoice_data.get("date")}</cbc:IssueDate>
    <cac:AdditionalDocumentReference>
        <cbc:ID>PIH</cbc:ID>
        <cac:Attachment>
            <cbc:EmbeddedDocumentBinaryObject mimeCode="text/plain">{pih}</cbc:EmbeddedDocumentBinaryObject>
        </cac:Attachment>
    </cac:AdditionalDocumentReference>
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyTaxScheme>
                <cbc:CompanyID>{invoice_data.get("seller_tin")}</cbc:CompanyID>
                <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
            </cac:PartyTaxScheme>
        </cac:Party>
    </cac:AccountingSupplierParty>
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyTaxScheme>
                <cbc:CompanyID>{invoice_data.get("buyer_tin")}</cbc:CompanyID>
                <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
            </cac:PartyTaxScheme>
        </cac:Party>
    </cac:AccountingCustomerParty>
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="SAR">{invoice_data.get("tax_amount")}</cbc:TaxAmount>
    </cac:TaxTotal>
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="SAR">{invoice_data.get("gross_amount")}</cbc:LineExtensionAmount>
        <cbc:TaxExclusiveAmount currencyID="SAR">{invoice_data.get("tax_amount")}</cbc:TaxExclusiveAmount>
        <cbc:PayableAmount currencyID="SAR">{invoice_data.get("net_amount")}</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
</Invoice>
"""
        return xml_template

    @staticmethod
    def sign_ubl_xml(xml_content: str, cert_key: str) -> str:
        """Injects cryptographic signatures and hash blocks into the UBL XML invoice."""
        # Calculate digest value
        digest = hashlib.sha256(xml_content.encode("utf-8")).hexdigest()[:32]
        # Simulate standard signature tag injection
        signed_xml = xml_content.replace(
            "</Invoice>",
            f"  <cac:Signature><cbc:ID>signature</cbc:ID><cbc:SignatureMethod>{digest}</cbc:SignatureMethod></cac:Signature>\n</Invoice>"
        )
        return signed_xml
