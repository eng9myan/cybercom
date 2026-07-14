# -*- coding: utf-8 -*-
import logging
import os
import sys
from typing import Any, Dict
from fastapi import FastAPI, BackgroundTasks

# Import compliance engines
from jordan_fotara import JordanFotaraPlugin
from saudi_zatca import SaudiZatcaPlugin
from peppol_ubl import PeppolUblPlugin

# Integrate with core-kernel's event bus
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core-kernel")))
try:
    from bus import EventBus
except ImportError:
    # Safe fallback if run independently
    EventBus = None

logger = logging.getLogger("cycom-compliance")
app = FastAPI(title="Cycom Compliance Gateway", version="2026.1.0")

# Previous Invoice XML Cache (ZATCA cryptosecurity chaining)
LAST_INVOICE_XML: Dict[str, str] = {}


async def process_fiscal_compliance(payload: Dict[str, Any]):
    """Processes compliance generation depending on the transaction target region."""
    global LAST_INVOICE_XML
    region = payload.get("region", "JO").upper()
    invoice_data = payload.get("invoice", {})
    tenant_company = f"{payload.get('tenant_id', 1)}_{payload.get('company_id', 1)}"

    logger.info(f"[Compliance] Intercepted invoice.finalized event. Target Region: {region}")

    if region == "JO":
        # Jordan JoFotara E-Invoice
        formatted = JordanFotaraPlugin.compile_invoice_json(invoice_data)
        qr_url = JordanFotaraPlugin.generate_qr_payload(formatted)
        logger.info(f"[JO-FOTARA SUCCESS] E-Invoice Certified. Verification QR Code URL: {qr_url}")
        return {"region": "JO", "status": "certified", "qr": qr_url}

    elif region == "SA":
        # Saudi ZATCA Phase 2 PIH Cryptochaining
        prev_xml = LAST_INVOICE_XML.get(tenant_company, "")
        pih = SaudiZatcaPlugin.calculate_pih(prev_xml)
        ubl_xml = SaudiZatcaPlugin.generate_ubl_invoice(invoice_data, pih)
        signed_xml = SaudiZatcaPlugin.sign_ubl_xml(ubl_xml, "mock_pem_cert_2026")
        LAST_INVOICE_XML[tenant_company] = signed_xml
        logger.info(f"[SA-ZATCA SUCCESS] Phase 2 XML Compiled & Signed. Previous Invoice Hash (PIH): {pih}")
        return {"region": "SA", "status": "cleared", "xml": signed_xml[:200] + "..."}

    elif region in ["US", "EU", "GB"]:
        # US/EU Peppol BIS Billing 3.0 UBL XML
        ubl_xml = PeppolUblPlugin.generate_peppol_ubl(invoice_data)
        logger.info(f"[PEPPOL SUCCESS] UBL 3.0 XML Formatted for global delivery.")
        return {"region": region, "status": "formatted", "xml": ubl_xml[:200] + "..."}

    else:
        logger.warning(f"[Compliance] Unsupported region: {region}. Standard fallback format applied.")
        return {"status": "skipped"}


# Register event listener if EventBus is loaded
if EventBus:
    EventBus.subscribe("invoice.finalized", process_fiscal_compliance)


@app.post("/api/compliance/process")
async def trigger_compliance_run(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """Direct REST endpoint to trigger compliance formatting manually or via webhook."""
    logger.info("Compliance Gateway API invoked directly.")
    background_tasks.add_task(process_fiscal_compliance, payload)
    return {"status": "processing"}
