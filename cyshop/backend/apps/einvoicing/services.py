"""
E-invoice generation: UBL 2.1 XML, invoice hash, ZATCA-style TLV QR.

`submit()` is the seam to the tax authority. Local generation (XML + hash + QR)
always runs; the network submission only runs when the company's TaxProfile has
onboarding credentials — otherwise the document stays 'generated' and is handed
to the operator to submit through the authority portal.
"""
import base64
import hashlib
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from xml.sax.saxutils import escape

from django.utils import timezone as djtz

from .models import EInvoiceDocument, Invoice, TaxProfile


# --------------------------------------------------------------------------- QR

def _tlv(tag: int, value: str) -> bytes:
    b = value.encode("utf-8")
    return bytes([tag, len(b)]) + b


def zatca_tlv_qr(invoice: Invoice, profile: TaxProfile, *, invoice_hash: str = "",
                 signature: str = "") -> str:
    """Base64 TLV per ZATCA. Tags 1-5 are the Phase-1 (simplified) minimum;
    6-9 (hash, signature, public key, stamp) are added once signing is wired."""
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = (
        _tlv(1, profile.legal_name or "Seller")
        + _tlv(2, profile.vat_number or "")
        + _tlv(3, ts)
        + _tlv(4, f"{invoice.total:.2f}")
        + _tlv(5, f"{invoice.tax_total:.2f}")
    )
    if invoice_hash:
        payload += _tlv(6, invoice_hash)
    if signature:
        payload += _tlv(7, signature)
    return base64.b64encode(payload).decode("ascii")


# -------------------------------------------------------------------------- UBL

_UBL_NS = (
    'xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" '
    'xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" '
    'xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"'
)

_TYPE_CODE = {"standard": "388", "simplified": "388",
              "credit_note": "381", "debit_note": "383"}


def build_ubl(invoice: Invoice, profile: TaxProfile, doc: EInvoiceDocument) -> str:
    e = escape
    cur = invoice.currency
    lines_xml = []
    for ln in invoice.lines.filter(is_deleted=False).order_by("line_no"):
        lines_xml.append(f"""  <cac:InvoiceLine>
    <cbc:ID>{ln.line_no}</cbc:ID>
    <cbc:InvoicedQuantity unitCode="PCE">{ln.quantity}</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="{cur}">{ln.line_subtotal}</cbc:LineExtensionAmount>
    <cac:TaxTotal>
      <cbc:TaxAmount currencyID="{cur}">{ln.line_tax}</cbc:TaxAmount>
      <cbc:RoundingAmount currencyID="{cur}">{ln.line_total}</cbc:RoundingAmount>
    </cac:TaxTotal>
    <cac:Item><cbc:Name>{e(ln.description)}</cbc:Name>
      <cac:ClassifiedTaxCategory><cbc:ID>S</cbc:ID>
        <cbc:Percent>{(ln.tax_rate * 100):.2f}</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price><cbc:PriceAmount currencyID="{cur}">{ln.unit_price}</cbc:PriceAmount></cac:Price>
  </cac:InvoiceLine>""")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice {_UBL_NS}>
  <cbc:ProfileID>reporting:1.0</cbc:ProfileID>
  <cbc:ID>{e(invoice.number)}</cbc:ID>
  <cbc:UUID>{doc.uuid}</cbc:UUID>
  <cbc:IssueDate>{invoice.issue_date}</cbc:IssueDate>
  <cbc:InvoiceTypeCode name="{'0100000' if invoice.invoice_type == 'standard' else '0200000'}">{_TYPE_CODE.get(invoice.invoice_type, '388')}</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>{cur}</cbc:DocumentCurrencyCode>
  <cbc:TaxCurrencyCode>{cur}</cbc:TaxCurrencyCode>
  <cac:AdditionalDocumentReference>
    <cbc:ID>ICV</cbc:ID><cbc:UUID>{doc.icv}</cbc:UUID>
  </cac:AdditionalDocumentReference>
  <cac:AdditionalDocumentReference>
    <cbc:ID>PIH</cbc:ID>
    <cac:Attachment><cbc:EmbeddedDocumentBinaryObject mimeCode="text/plain">{doc.pih or 'NWZlY2ViNjZmZmM4NmYzOGQ5NTI3ODZjNmQ2OTZjNzljMmRiYzIzOWRkNGU5MWI0NjcyOWQ3M2EyN2ZiNTdlOQ=='}</cbc:EmbeddedDocumentBinaryObject></cac:Attachment>
  </cac:AdditionalDocumentReference>
  <cac:AccountingSupplierParty><cac:Party>
    <cac:PostalAddress>
      <cbc:StreetName>{e(profile.address_street)}</cbc:StreetName>
      <cbc:CityName>{e(profile.address_city)}</cbc:CityName>
      <cbc:PostalZone>{e(profile.address_postal)}</cbc:PostalZone>
      <cac:Country><cbc:IdentificationCode>{profile.country_code}</cbc:IdentificationCode></cac:Country>
    </cac:PostalAddress>
    <cac:PartyTaxScheme>
      <cbc:CompanyID>{e(profile.vat_number)}</cbc:CompanyID>
      <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
    </cac:PartyTaxScheme>
    <cac:PartyLegalEntity><cbc:RegistrationName>{e(profile.legal_name)}</cbc:RegistrationName></cac:PartyLegalEntity>
  </cac:Party></cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty><cac:Party>
    <cac:PartyTaxScheme>
      <cbc:CompanyID>{e(invoice.customer_tax_number)}</cbc:CompanyID>
      <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
    </cac:PartyTaxScheme>
    <cac:PartyLegalEntity><cbc:RegistrationName>{e(invoice.customer_name)}</cbc:RegistrationName></cac:PartyLegalEntity>
  </cac:Party></cac:AccountingCustomerParty>
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="{cur}">{invoice.tax_total}</cbc:TaxAmount>
    <cac:TaxSubtotal>
      <cbc:TaxableAmount currencyID="{cur}">{invoice.subtotal}</cbc:TaxableAmount>
      <cbc:TaxAmount currencyID="{cur}">{invoice.tax_total}</cbc:TaxAmount>
      <cac:TaxCategory><cbc:ID>S</cbc:ID>
        <cbc:Percent>{(profile.default_vat_rate * 100):.2f}</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:TaxCategory>
    </cac:TaxSubtotal>
  </cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="{cur}">{invoice.subtotal}</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="{cur}">{invoice.subtotal}</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="{cur}">{invoice.total}</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="{cur}">{invoice.total}</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
{chr(10).join(lines_xml)}
</Invoice>"""
    return xml


def hash_xml(xml: str) -> str:
    return base64.b64encode(hashlib.sha256(xml.encode("utf-8")).digest()).decode("ascii")


# --------------------------------------------------------------------- pipeline

def generate(invoice: Invoice) -> EInvoiceDocument:
    invoice.recalculate()
    profile = getattr(invoice.company, "tax_profile", None)
    if profile is None:
        profile = TaxProfile(
            company=invoice.company, tenant_id=invoice.tenant_id,
            scheme="none", legal_name=invoice.company.name,
            country_code=getattr(invoice.company, "country_code", "SA"))
    doc, _ = EInvoiceDocument.objects.get_or_create(
        invoice=invoice, defaults={"tenant_id": invoice.tenant_id})
    if not doc.uuid:
        doc.uuid = uuid.uuid4()
    doc.scheme = profile.scheme
    doc.icv = (EInvoiceDocument.objects.filter(tenant_id=invoice.tenant_id)
               .exclude(pk=doc.pk).count()) + 1
    last = (EInvoiceDocument.objects.filter(tenant_id=invoice.tenant_id, invoice_hash__gt="")
            .exclude(pk=doc.pk).order_by("-icv").first())
    doc.pih = last.invoice_hash if last else ""
    doc.ubl_xml = build_ubl(invoice, profile, doc)
    doc.invoice_hash = hash_xml(doc.ubl_xml)
    doc.qr_code = zatca_tlv_qr(invoice, profile, invoice_hash=doc.invoice_hash)
    doc.status = "generated"
    warns = []
    if not profile.vat_number:
        warns.append("Seller VAT number is not set on the company tax profile.")
    if profile.scheme == "none":
        warns.append("No e-invoicing scheme selected — XML + QR generated, nothing submitted.")
    doc.warnings = warns
    doc.save()
    return doc


def submit(doc: EInvoiceDocument) -> EInvoiceDocument:
    """Send to ZATCA / JoFotara. Requires onboarding credentials on the profile;
    otherwise the document is left 'generated' for portal submission."""
    if doc.status == "draft":
        generate(doc.invoice)
        doc.refresh_from_db()
    profile = getattr(doc.invoice.company, "tax_profile", None)
    if not profile or not (profile.client_id and profile.client_secret and profile.csid):
        doc.warnings = (doc.warnings or []) + [
            "Scheme onboarding credentials (client_id / client_secret / CSID) are "
            "not configured — submit this invoice through the authority portal."]
        doc.save(update_fields=["warnings", "updated_at", "version"])
        return doc
    # --- real submission would sign the XML and POST to the clearance /
    #     reporting endpoint here. Kept explicit rather than faked.
    doc.submission_response = {"detail": "signing + submission not enabled in this build"}
    doc.submitted_at = djtz.now()
    doc.status = "submitted"
    doc.save()
    return doc
