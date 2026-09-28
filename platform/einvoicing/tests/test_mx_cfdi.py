"""
CFDI 4.0 (Mexico) builder + sello tests.

Every sealed document is validated against SAT's cfdv40.xsd with the full
SAT catalogues (so product keys / units / postal codes are checked against
the real c_ClaveProdServ / c_ClaveUnidad / c_CodigoPostal), and every sello
is verified against the cadena original produced by SAT's own XSLT.
"""
import base64
import datetime as dt
from decimal import Decimal

import pytest
from lxml import etree

from platform.einvoicing.national import EInvoiceDataMissing, TransportNotConfigured
from platform.einvoicing.national.base import DocInput, LineInput, PartyInput
from platform.einvoicing.national.mx_cfdi import MxCfdi, cadena_original

FMT = MxCfdi()
CFDI = "{http://www.sat.gob.mx/cfd/4}"
NO_CERT = "30001000000500003416"
ORIGINAL_UUID = "5FB2822E-396D-4725-8521-CDC4BDD20CCF"


def _sat_like_csd(serial_digits=NO_CERT):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "CYCOM MEXICO TEST")])
    now = dt.datetime.now(dt.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(int.from_bytes(serial_digits.encode("ascii"), "big"))
            .not_valid_before(now - dt.timedelta(days=1)).not_valid_after(now + dt.timedelta(days=365))
            .sign(key, hashes.SHA256()))
    # SAT ships the key as DER, PKCS#8, password-protected -- mirror that.
    key_der = key.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8,
                                serialization.BestAvailableEncryption(b"12345678a"))
    return key_der, cert.public_bytes(serialization.Encoding.DER), cert


@pytest.fixture
def csd(tmp_path, monkeypatch):
    key_der, cert_der, cert = _sat_like_csd()
    (tmp_path / "csd.key").write_bytes(key_der)
    (tmp_path / "csd.cer").write_bytes(cert_der)
    monkeypatch.setenv("CFDI_CSD_PRIVATE_KEY_PATH", str(tmp_path / "csd.key"))
    monkeypatch.setenv("CFDI_CSD_CERT_PATH", str(tmp_path / "csd.cer"))
    monkeypatch.setenv("CFDI_CSD_KEY_PASSWORD", "12345678a")
    return cert


def _seller(**extra):
    return PartyInput(tax_id="EKU9003173C9", name="ESCUELA KEMPER URGATE", postal_code="06600",
                      country_code="MX", extra={"regimen_fiscal": "601", "forma_pago": "03",
                                                "metodo_pago": "PUE", "default_clave_prod_serv": "84111506",
                                                "default_clave_unidad": "E48", **extra})


def _buyer(**kw):
    base = dict(tax_id="URE180429TM6", name="UNIVERSIDAD ROBOTICA ESPAÑOLA", postal_code="86991",
                country_code="MX", extra={"regimen_fiscal": "601", "uso_cfdi": "G03"})
    base.update(kw)
    return PartyInput(**base)


def _doc(**kw):
    base = dict(
        number="F-000123", issue_dt=dt.datetime(2026, 9, 1, 10, 30, 0), currency="MXN",
        seller=_seller(), buyer=_buyer(),
        lines=[
            LineInput("Servicios de consultoría", Decimal("10"), Decimal("1000.00"), Decimal("16")),
            LineInput("Capacitación", Decimal("1"), Decimal("2500.50"), Decimal("16")),
        ],
    )
    base.update(kw)
    return DocInput(**base)


def _sealed(doc):
    return FMT.sign(FMT.build(doc), doc)


def _root(xml):
    return etree.fromstring(xml.encode("utf-8"))


def test_sealed_invoice_is_valid_against_sat_xsd_and_catalogues(csd):
    xml = _sealed(_doc())
    assert FMT.schema_errors(xml) == []
    root = _root(xml)
    assert root.get("NoCertificado") == NO_CERT
    assert root.get("TipoDeComprobante") == "I"
    assert (root.get("Serie"), root.get("Folio")) == ("F-", "000123")


def test_sello_verifies_against_sats_cadena_original(csd):
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    root = _root(_sealed(_doc()))
    cadena = cadena_original(root)
    assert cadena.startswith("||4.0|F-|000123|2026-09-01T10:30:00|03|")
    sello = base64.b64decode(root.get("Sello"))
    csd.public_key().verify(sello, cadena.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())

    # tampering with a sealed amount breaks the seal
    root.set("Total", "1.00")
    with pytest.raises(Exception):
        csd.public_key().verify(sello, cadena_original(root).encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())


def test_totals_and_tax_breakdown(csd):
    root = _root(_sealed(_doc()))
    # 10000 + 2500.50 = 12500.50 ; IVA 16% = 1600 + 400.08 = 2000.08
    assert root.get("SubTotal") == "12500.50"
    assert root.get("Total") == "14500.58"
    imps = root.find(f"{CFDI}Impuestos")
    assert imps.get("TotalImpuestosTrasladados") == "2000.08"
    tr = imps.find(f"{CFDI}Traslados/{CFDI}Traslado")
    assert (tr.get("TasaOCuota"), tr.get("Base"), tr.get("Importe")) == ("0.160000", "12500.50", "2000.08")


def test_zero_rate_treatments(csd):
    lines = [
        LineInput("Alimento", Decimal("1"), Decimal("100"), Decimal("0"), extra={"tratamiento_cero": "tasa0"}),
        LineInput("Colegiatura", Decimal("1"), Decimal("200"), Decimal("0"), extra={"tratamiento_cero": "exento"}),
        LineInput("Donativo", Decimal("1"), Decimal("50"), Decimal("0"), extra={"tratamiento_cero": "no_objeto"}),
    ]
    xml = _sealed(_doc(lines=lines))
    assert FMT.schema_errors(xml) == []
    concepts = _root(xml).findall(f"{CFDI}Conceptos/{CFDI}Concepto")
    assert [c.get("ObjetoImp") for c in concepts] == ["02", "02", "01"]
    factors = {t.get("TipoFactor") for t in _root(xml).findall(f"{CFDI}Impuestos/{CFDI}Traslados/{CFDI}Traslado")}
    assert factors == {"Tasa", "Exento"}


def test_zero_rated_line_without_treatment_is_refused(csd):
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(_doc(lines=[LineInput("x", Decimal("1"), Decimal("1"), Decimal("0"))]))
    assert any(p["key"] == "tratamiento_cero" for p in exc.value.problems)


def test_sale_to_the_general_public(csd):
    xml = _sealed(_doc(buyer=PartyInput(name="Cliente mostrador", country_code="MX")))
    assert FMT.schema_errors(xml) == []
    root = _root(xml)
    rc = root.find(f"{CFDI}Receptor")
    assert (rc.get("Rfc"), rc.get("Nombre"), rc.get("UsoCFDI")) == ("XAXX010101000", "PUBLICO EN GENERAL", "S01")
    assert rc.get("DomicilioFiscalReceptor") == "06600"
    assert root.find(f"{CFDI}InformacionGlobal").get("Meses") == "09"


def test_foreign_buyer(csd):
    with pytest.raises(EInvoiceDataMissing):
        FMT.build(_doc(buyer=PartyInput(name="ACME Inc", country_code="US", tax_id="")))
    xml = _sealed(_doc(buyer=PartyInput(name="ACME Inc", country_code="US",
                                        extra={"residencia_fiscal": "USA", "num_reg_id_trib": "123456789"})))
    assert FMT.schema_errors(xml) == []
    rc = _root(xml).find(f"{CFDI}Receptor")
    assert (rc.get("Rfc"), rc.get("ResidenciaFiscal")) == ("XEXX010101000", "USA")


def test_credit_note_is_egreso_related_to_the_original_uuid(csd):
    with pytest.raises(EInvoiceDataMissing):
        FMT.build(_doc(is_credit_note=True))
    xml = _sealed(_doc(is_credit_note=True, number="NC-000007", extra={"original_reference": ORIGINAL_UUID}))
    assert FMT.schema_errors(xml) == []
    root = _root(xml)
    assert root.get("TipoDeComprobante") == "E"
    rel = root.find(f"{CFDI}CfdiRelacionados")
    assert rel.get("TipoRelacion") == "01"
    assert rel.find(f"{CFDI}CfdiRelacionado").get("UUID") == ORIGINAL_UUID


def test_foreign_currency_needs_tipo_de_cambio(csd):
    with pytest.raises(EInvoiceDataMissing):
        FMT.build(_doc(currency="USD"))
    xml = _sealed(_doc(currency="USD", extra={"tipo_cambio": "17.2531"}))
    assert FMT.schema_errors(xml) == []
    assert _root(xml).get("TipoCambio") == "17.2531"


def test_ppd_forces_forma_pago_99(csd):
    xml = _sealed(_doc(seller=_seller(metodo_pago="PPD")))
    assert FMT.schema_errors(xml) == []
    assert _root(xml).get("FormaPago") == "99"


def test_catalogue_validation_is_real(csd):
    """A product key that isn't in SAT's c_ClaveProdServ fails the schema."""
    doc = _doc(lines=[LineInput("x", Decimal("1"), Decimal("10"), Decimal("16"),
                                extra={"clave_prod_serv": "99999999"})])
    assert FMT.schema_errors(_sealed(doc))


def test_non_mexican_rate_refused():
    with pytest.raises(EInvoiceDataMissing):
        FMT.build(_doc(lines=[LineInput("x", Decimal("1"), Decimal("10"), Decimal("19"))]))


def test_missing_csd_is_a_preflight_problem(monkeypatch):
    monkeypatch.delenv("CFDI_CSD_PRIVATE_KEY_PATH", raising=False)
    monkeypatch.delenv("CFDI_CSD_CERT_PATH", raising=False)
    problems = FMT.signing_problems(_doc())
    assert problems and problems[0]["key"] == "certificate"


def test_non_sat_certificate_is_refused(tmp_path, monkeypatch):
    key_der, cert_der, _ = _sat_like_csd(serial_digits="ABC")
    (tmp_path / "k").write_bytes(key_der)
    (tmp_path / "c").write_bytes(cert_der)
    monkeypatch.setenv("CFDI_CSD_PRIVATE_KEY_PATH", str(tmp_path / "k"))
    monkeypatch.setenv("CFDI_CSD_CERT_PATH", str(tmp_path / "c"))
    monkeypatch.setenv("CFDI_CSD_KEY_PASSWORD", "12345678a")
    assert FMT.signing_problems(_doc())


def test_engine_reports_incomplete_without_csd_and_burns_no_sequence(db, monkeypatch):
    import uuid as _uuid

    from platform.einvoicing.engine import clear_national
    from platform.einvoicing.models import EInvoiceSequence

    monkeypatch.delenv("CFDI_CSD_PRIVATE_KEY_PATH", raising=False)
    tenant = _uuid.uuid4()
    res = clear_national(tenant_id=tenant, scope="default", mode="mx_cfdi", doc=_doc())
    assert res.status == "incomplete"
    assert not EInvoiceSequence.objects.filter(tenant_id=tenant).exists()


def test_engine_with_csd_and_no_pac_generates_a_sealed_valid_cfdi(db, csd, monkeypatch):
    import uuid as _uuid

    from platform.einvoicing.engine import clear_national

    monkeypatch.delenv("CFDI_PAC_BASE_URL", raising=False)
    res = clear_national(tenant_id=_uuid.uuid4(), scope="default", mode="mx_cfdi", doc=_doc())
    assert res.status == "generated", res.error
    assert FMT.schema_errors(res.document) == []
    assert _root(res.document).get("Sello")


def test_unconfigured_pac_refuses(monkeypatch):
    monkeypatch.delenv("CFDI_PAC_BASE_URL", raising=False)
    with pytest.raises(TransportNotConfigured):
        FMT.submit("<x/>", _doc())
