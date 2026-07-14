# -*- coding: utf-8 -*-
from decimal import Decimal
import logging

logger = logging.getLogger("cycom-localization")


class FiscalLocalizationEngine:
    """Manages global tax calculations, currencies, and pluggable compliance rules."""

    @staticmethod
    def get_regional_tax_rate(country_code: str) -> Decimal:
        """Returns the default VAT / Sales Tax percentage for the region."""
        code = country_code.upper()
        if code == "JO":
            return Decimal("16.0")  # Jordan 16% VAT
        elif code == "SA":
            return Decimal("15.0")  # Saudi 15% VAT
        elif code == "EU":
            return Decimal("20.0")  # Europe average 20% VAT
        elif code == "US":
            return Decimal("8.25")  # Simulated US State Sales Tax
        else:
            return Decimal("0.0")   # Zero-tax default

    @staticmethod
    def calculate_invoice_tax(country_code: str, amount_untaxed: Decimal) -> dict:
        """Calculates tax amounts and final totals based on regional tax laws."""
        rate_pct = FiscalLocalizationEngine.get_regional_tax_rate(country_code)
        rate = rate_pct / Decimal("100.0")

        # In the US, sales tax is calculated but purchase bills have 0% input tax
        # We simulate standard VAT calculation for Jordan, Saudi, and EU
        tax_amount = amount_untaxed * rate
        total = amount_untaxed + tax_amount

        return {
            "rate_percent": float(rate_pct),
            "tax_amount": round(float(tax_amount), 2),
            "total_amount": round(float(total), 2)
        }

    @staticmethod
    def get_default_esign_template(country_code: str) -> dict:
        """Returns localized digital signature configuration and templates."""
        code = country_code.upper()
        if code == "JO":
            return {
                "template_name": "Jordanian Civil Service Agreement",
                "signing_authority": "Ministry of Digital Economy (MoDE)",
                "algorithm": "RSASSA-PSS",
                "hash_func": "SHA256"
            }
        elif code == "SA":
            return {
                "template_name": "Saudi Commercial Purchase Order Agreement",
                "signing_authority": "Saudi National Center for Digital Certification (NCDC)",
                "algorithm": "ECDSA",
                "hash_func": "SHA384"
            }
        elif code == "EU":
            return {
                "template_name": "eIDAS Compliant Corporate Resolution",
                "signing_authority": "European Trusted List (EUTL)",
                "algorithm": "Ed25519",
                "hash_func": "SHA512"
            }
        else:
            return {
                "template_name": "Standard B2B Non-Disclosure Agreement",
                "signing_authority": "Self-Signed Corporate CA",
                "algorithm": "RSASSA-PKCS1-v1_5",
                "hash_func": "SHA256"
            }
