"""
CyberCom e-invoicing clearance engine.

Mode-pluggable per country (see docs/blueprint/specs/einvoicing-clearance-engine.md):
  jo_jofotara  — Jordan ISTD JoFotara (UBL 2.1, PINT-JO)      [implemented]
  sa_zatca     — Saudi ZATCA Phase 2 (UBL 2.1, clearance/reporting)  [planned]
  ae_peppol    — UAE federal e-invoicing (Peppol BIS 3.0)      [planned]

Public entry point: `platform.einvoicing.engine.clear_invoice(invoice, mode=...)`.
"""

default_app_config = "platform.einvoicing.apps.EInvoicingConfig"
