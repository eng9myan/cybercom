"""
CyberCom e-invoicing clearance engine.

Mode-pluggable per country (see docs/blueprint/specs/einvoicing-clearance-engine.md):
  jo_jofotara  — Jordan ISTD JoFotara (UBL 2.1, PINT-JO, XAdES-B)     [implemented]
  sa_zatca     — Saudi ZATCA Phase 2 (UBL 2.1, TLV QR, ECDSA stamp,
                 clearance for B2B / reporting for B2C)                [implemented]
  ae_peppol    — UAE federal e-invoicing (Peppol BIS 3.0)             [planned]

Both implemented modes still need their regulator conformance cycle before
production: JO — XSD/Schematron + ISTD sandbox onboarding; SA — the full
UBLExtensions signature block + ZATCA CSID compliance onboarding.

Public entry point: `platform.einvoicing.engine.clear_invoice(invoice, mode=...)`.
"""

default_app_config = "platform.einvoicing.apps.EInvoicingConfig"
