# -*- coding: utf-8 -*-
import json
import xml.etree.ElementTree as ET
from decimal import Decimal
from typing import Dict, Any

class TaxEngine:
    """Enterprise Tax & Localization Compliance Engine (JoFotara compatible)."""
    
    @staticmethod
    def calculate_invoice_taxes(
        amount: Decimal, 
        vat_rate: Decimal = Decimal("0.16"), 
        wht_rate: Decimal = Decimal("0.02"), 
        apply_wht: bool = False
    ) -> Dict[str, Any]:
        """Calculate VAT and WHT values."""
        vat_amount = amount * vat_rate
        wht_amount = amount * wht_rate if apply_wht else Decimal("0")
        total = amount + vat_amount - wht_amount
        
        return {
            "base_amount": float(amount),
            "vat_rate": float(vat_rate),
            "vat_amount": float(vat_amount),
            "wht_rate": float(wht_rate),
            "wht_amount": float(wht_amount),
            "total_amount": float(total)
        }
        
    @staticmethod
    def generate_jofotara_xml(invoice_data: Dict[str, Any]) -> str:
        """Generate Jordan JoFotara e-invoicing compliant XML envelope."""
        root = ET.Element("Invoice", xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2")
        
        id_elem = ET.SubElement(root, "ID")
        id_elem.text = str(invoice_data.get("invoice_number", "INV-UNKNOWN"))
        
        date_elem = ET.SubElement(root, "IssueDate")
        date_elem.text = str(invoice_data.get("issue_date", "2026-07-14"))
        
        tax_elem = ET.SubElement(root, "TaxTotal")
        tax_amt = ET.SubElement(tax_elem, "TaxAmount", currencyID="JOD")
        tax_amt.text = f"{invoice_data.get('vat_amount', 0.0):.3f}"
        
        legal_elem = ET.SubElement(root, "LegalMonetaryTotal")
        payable = ET.SubElement(legal_elem, "PayableAmount", currencyID="JOD")
        payable.text = f"{invoice_data.get('total_amount', 0.0):.3f}"
        
        return ET.tostring(root, encoding="utf-8").decode("utf-8")
