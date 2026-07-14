# -*- coding: utf-8 -*-
import base64
import hashlib


class JordanFotaraPlugin:
    """Jordan ISTD JoFotara E-Invoicing Compliance Plugin."""

    @staticmethod
    def compile_invoice_json(invoice_data: dict) -> dict:
        """Structures invoice fields into ISTD-compliant JSON format."""
        return {
            "invoiceHeader": {
                "invoiceNumber": invoice_data.get("number"),
                "issueDate": invoice_data.get("date"),
                "uuid": invoice_data.get("uuid"),
                "invoiceType": "388",  # Standard Tax Invoice
            },
            "sellerDetails": {
                "tin": invoice_data.get("seller_tin"),
                "name": invoice_data.get("seller_name"),
            },
            "buyerDetails": {
                "tin": invoice_data.get("buyer_tin"),
                "name": invoice_data.get("buyer_name"),
            },
            "taxSummary": {
                "grossAmount": float(invoice_data.get("gross_amount", 0.0)),
                "taxAmount": float(invoice_data.get("tax_amount", 0.0)),
                "netAmount": float(invoice_data.get("net_amount", 0.0)),
            },
            "items": [
                {
                    "name": item.get("name"),
                    "quantity": int(item.get("qty", 1)),
                    "unitPrice": float(item.get("price", 0.0)),
                    "taxRate": float(item.get("tax_rate", 0.16)),
                }
                for item in invoice_data.get("items", [])
            ],
        }

    @staticmethod
    def generate_qr_payload(payload: dict) -> str:
        """Compiles the ISTD validation URL to render as a QR code."""
        tin = payload["sellerDetails"]["tin"]
        inv_no = payload["invoiceHeader"]["invoiceNumber"]
        net_amt = payload["taxSummary"]["netAmount"]
        # Official ISTD test environment validation link format
        verify_url = f"https://jofotara.gov.jo/verify?tin={tin}&inv={inv_no}&amt={net_amt}"
        return verify_url
