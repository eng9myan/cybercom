"""
Zakata — Saudi ZATCA E-Invoicing Integration (Fatoorah).
Compliant with Saudi Arabia's ZATCA e-invoicing regulations
(Phase 1 & Phase 2) for healthcare providers.
"""
import base64
import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger("cybercom.integrations.zakata")


class ZATCAClient:
    """
    Saudi ZATCA Fatoorah API client for e-invoicing.
    """

    SANDBOX_BASE = "https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal"
    PRODUCTION_BASE = "https://gw-fatoora.zatca.gov.sa/e-invoicing/core"

    def __init__(self, sandbox: bool = True):
        self.base_url = self.SANDBOX_BASE if sandbox else self.PRODUCTION_BASE
        self.api_key = getattr(settings, "ZATCA_API_KEY", "")
        self.csid = getattr(settings, "ZATCA_CSID", "")
        self.secret = getattr(settings, "ZATCA_SECRET", "")
        self.timeout = 30

    def _headers(self) -> dict[str, str]:
        token = self._get_token()
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Language": "en",
            "Authorization": f"Bearer {token}",
            "OTP": self.api_key,
        }

    def _get_token(self) -> str:
        url = f"{self.base_url}/compliance"
        try:
            resp = requests.post(
                url,
                json={"csid": self.csid, "secret": self.secret},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json().get("token", "")
        except Exception as exc:
            logger.error("ZATCA token fetch failed: %s", exc)
            return ""

    def report_invoice(self, invoice_xml: str) -> dict[str, Any]:
        """Report a cleared invoice (Phase 2)."""
        url = f"{self.base_url}/invoices/reporting/single"
        try:
            resp = requests.post(
                url,
                data=invoice_xml,
                headers={**self._headers(), "Content-Type": "application/xml"},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.error("ZATCA invoice reporting failed: %s", exc)
            return {"error": str(exc), "status": "failed"}

    def clear_invoice(self, invoice_xml: str) -> dict[str, Any]:
        """Clear a B2B invoice (Phase 2)."""
        url = f"{self.base_url}/invoices/clearance/single"
        try:
            resp = requests.post(
                url,
                data=invoice_xml,
                headers={**self._headers(), "Content-Type": "application/xml"},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.error("ZATCA invoice clearance failed: %s", exc)
            return {"error": str(exc), "status": "failed"}

    def validate_xml(self, invoice_xml: str) -> dict[str, Any]:
        """Validate invoice XML against ZATCA rules."""
        url = f"{self.base_url}/validation/invoices"
        try:
            resp = requests.post(
                url,
                data=invoice_xml,
                headers={**self._headers(), "Content-Type": "application/xml"},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.error("ZATCA validation failed: %s", exc)
            return {"error": str(exc)}

    def generate_qr(self, invoice_data: dict[str, Any]) -> str:
        """Generate ZATCA-compliant QR code data (Base64 TLV)."""
        try:
            import json
            tlv = self._build_tlv(invoice_data)
            return base64.b64encode(tlv).decode("ascii")
        except Exception as exc:
            logger.error("ZATCA QR generation failed: %s", exc)
            return ""

    def _build_tlv(self, data: dict[str, Any]) -> bytes:
        """Build TLV bytes for ZATCA QR code."""
        fields = []
        # Tag 1: Seller Name
        seller = data.get("seller_name", "").encode("utf-8")
        fields.append(bytes([1, len(seller)]) + seller)
        # Tag 2: VAT Registration Number
        vat = data.get("vat_number", "").encode("utf-8")
        fields.append(bytes([2, len(vat)]) + vat)
        # Tag 3: Timestamp
        ts = data.get("timestamp", "").encode("utf-8")
        fields.append(bytes([3, len(ts)]) + ts)
        # Tag 4: Total with VAT
        total = str(data.get("total_with_vat", 0)).encode("utf-8")
        fields.append(bytes([4, len(total)]) + total)
        # Tag 5: VAT Total
        vat_total = str(data.get("vat_total", 0)).encode("utf-8")
        fields.append(bytes([5, len(vat_total)]) + vat_total)
        return b"".join(fields)
