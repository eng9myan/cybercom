from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.tenants.models import Company, Tenant
from .models import Invoice, InvoiceLine, TaxProfile
from . import services


class _Ctx:
    def __init__(self, tid):
        self.tenant_id = tid


class EInvoiceTests(TestCase):
    def setUp(self):
        self.t = Tenant.objects.create(name="T", subdomain="t-einv")
        self.co = Company.objects.create(tenant_id=self.t.id, name="Acme", country_code="SA")

    def _invoice(self, **kw):
        inv = Invoice.objects.create(
            tenant_id=self.t.id, company=self.co, number=kw.get("number", "INV-1"),
            invoice_type="simplified", customer_name="Walk-in",
            issue_date=date(2026, 9, 1), currency="SAR")
        InvoiceLine.objects.create(tenant_id=self.t.id, invoice=inv, line_no=1,
                                   description="Widget", quantity=2, unit_price=25,
                                   tax_rate=Decimal("0.15"))
        inv.recalculate()
        return inv

    def test_totals(self):
        inv = self._invoice()
        self.assertEqual(inv.subtotal, Decimal("50.00"))
        self.assertEqual(inv.tax_total, Decimal("7.50"))
        self.assertEqual(inv.total, Decimal("57.50"))

    def test_generate_produces_xml_hash_qr(self):
        inv = self._invoice()
        doc = services.generate(inv)
        self.assertEqual(doc.status, "generated")
        self.assertTrue(doc.ubl_xml.startswith("<?xml"))
        self.assertIn("<cbc:TaxInclusiveAmount", doc.ubl_xml)
        self.assertTrue(doc.invoice_hash)
        self.assertTrue(doc.qr_code)          # base64 TLV
        # no scheme + no VAT -> two warnings, nothing submitted
        self.assertEqual(len(doc.warnings), 2)

    def test_submit_without_credentials_is_not_faked(self):
        inv = self._invoice()
        doc = services.generate(inv)
        doc = services.submit(doc)
        self.assertEqual(doc.status, "generated")   # not "submitted"
        self.assertTrue(any("portal" in w for w in doc.warnings))

    def test_hash_chain_advances(self):
        d1 = services.generate(self._invoice(number="A"))
        d2 = services.generate(self._invoice(number="B"))
        self.assertEqual(d2.pih, d1.invoice_hash)
        self.assertGreater(d2.icv, d1.icv)

    def test_sign_without_csid_warns_not_signed(self):
        from .signing import sign_document
        doc = services.generate(self._invoice())
        doc = sign_document(doc)
        self.assertNotEqual(doc.status, "signed")
        self.assertTrue(any("Not signed" in w for w in doc.warnings))

    def test_sign_with_csid_produces_xades(self):
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        import datetime
        from .signing import sign_document

        key = ec.generate_private_key(ec.SECP256K1())
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Acme")])
        cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                .public_key(key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(datetime.datetime.now(datetime.UTC))
                .not_valid_after(datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365))
                .sign(key, hashes.SHA256()))
        TaxProfile.objects.create(
            tenant_id=self.t.id, company=self.co, scheme="zatca", legal_name="Acme",
            vat_number="300000000000003",
            certificate_pem=cert.public_bytes(serialization.Encoding.PEM).decode(),
            private_key_pem=key.private_bytes(
                serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption()).decode())
        doc = services.generate(self._invoice())
        doc = sign_document(doc)
        self.assertEqual(doc.status, "signed")
        self.assertIn("ext:UBLExtensions", doc.signed_xml)
        self.assertIn("xades:SigningTime", doc.signed_xml)
        self.assertIn("ds:SignatureValue", doc.signed_xml)
