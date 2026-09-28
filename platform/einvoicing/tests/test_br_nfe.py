"""
NF-e 4.00 (Brazil, modelo 55) builder + signature tests. Every signed
document is validated against the SEFAZ schema package (PL_010 v1.30)
vendored under schemas/br/, and every signature is re-verified
independently (digest over C14N(infNFe) + RSA-SHA1 over C14N(SignedInfo)).
"""
import datetime as dt
from decimal import Decimal

import pytest
from lxml import etree

from platform.einvoicing.national import EInvoiceDataMissing, TransportNotConfigured
from platform.einvoicing.national.base import DocInput, LineInput, PartyInput
from platform.einvoicing.national.br_nfe import BrNfe, chave_dv, cnpj_valid, cpf_valid, verify_signature

FMT = BrNfe()
NFE = "{http://www.portalfiscal.inf.br/nfe}"
SELLER_CNPJ = "11222333000181"
BUYER_CNPJ = "33000167000101"


@pytest.fixture
def a1(tmp_path, monkeypatch):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import BestAvailableEncryption
    from cryptography.hazmat.primitives.serialization.pkcs12 import serialize_key_and_certificates
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, f"CYCOM BRASIL LTDA:{SELLER_CNPJ}")])
    now = dt.datetime.now(dt.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now - dt.timedelta(days=1))
            .not_valid_after(now + dt.timedelta(days=365)).sign(key, hashes.SHA256()))
    pfx = serialize_key_and_certificates(b"a1", key, cert, None, BestAvailableEncryption(b"senha"))
    (tmp_path / "a1.pfx").write_bytes(pfx)
    monkeypatch.setenv("NFE_PFX_PATH", str(tmp_path / "a1.pfx"))
    monkeypatch.setenv("NFE_PFX_PASSWORD", "senha")


def _seller(**extra):
    return PartyInput(
        tax_id=SELLER_CNPJ, name="CYCOM BRASIL LTDA", street="Avenida Paulista", building_number="1000",
        city="São Paulo", region="SP", postal_code="01310100", country_code="BR",
        extra={"ie": "123456789012", "crt": "3", "bairro": "Bela Vista", "codigo_municipio": "3550308",
               "serie": "1", "natureza_operacao": "Venda de mercadoria", "ambiente": "1", "ind_pres": "0",
               "forma_pagamento": "15", "default_origem": "0", "default_icms_situacao": "00",
               "default_pis_cst": "01", "default_cofins_cst": "01", "default_p_pis": "1.65",
               "default_p_cofins": "7.6", **extra})


def _buyer(**kw):
    base = dict(tax_id=BUYER_CNPJ, name="CLIENTE COMERCIAL SA", street="Rua do Ouvidor", building_number="50",
                city="Rio de Janeiro", region="RJ", postal_code="20040030", country_code="BR",
                extra={"ind_ie_dest": "1", "ie": "86543210", "bairro": "Centro", "codigo_municipio": "3304557"})
    base.update(kw)
    return PartyInput(**base)


def _line(name="Mercadoria", qty="10", price="100.00", **extra):
    return LineInput(name, Decimal(qty), Decimal(price), Decimal("0"),
                     extra={"ncm": "84713012", "cfop": "6102", "p_icms": "12", **extra})


def _doc(**kw):
    base = dict(number="INV-1", issue_dt=dt.datetime(2026, 9, 1, 10, 0), currency="BRL", icv=123,
                uuid="9b2f6f7e-1c1e-4b7a-9f0e-3f7e2b1a0c11", seller=_seller(), buyer=_buyer(), lines=[_line()])
    base.update(kw)
    return DocInput(**base)


def _signed(doc):
    return FMT.sign(FMT.build(doc), doc)


def _f(xml, path):
    root = etree.fromstring(xml.encode())
    return root.find("/".join(f"{NFE}{p}" for p in path.split("/")))


def test_check_digit_algorithms():
    assert cnpj_valid(SELLER_CNPJ) and cnpj_valid(BUYER_CNPJ)
    assert not cnpj_valid("11222333000182")
    assert cpf_valid("52998224725") and not cpf_valid("52998224726")
    assert cnpj_valid("12ABC34501DE35")   # Receita Federal's alphanumeric-CNPJ example
    # mod-11 access-key DV, remainder 0/1 -> 0
    assert chave_dv("0" * 43) == 0


def test_regime_normal_nfe_is_schema_valid_and_signed(a1):
    xml = _signed(_doc())
    assert FMT.schema_errors(xml) == []
    assert verify_signature(xml)
    inf = etree.fromstring(xml.encode()).find(f"{NFE}infNFe")
    chave = inf.get("Id")[3:]
    assert len(chave) == 44 and chave[20:22] == "55" and chave[22:25] == "001" and chave[25:34] == "000000123"
    assert chave_dv(chave[:43]) == int(chave[-1])
    assert _f(xml, "infNFe/ide/idDest").text == "2"        # SP -> RJ interestadual


def test_por_dentro_totals(a1):
    xml = _signed(_doc())
    t = _f(xml, "infNFe/total/ICMSTot")
    # vProd 1000.00; ICMS 12% = 120.00; PIS 1.65% = 16.50; COFINS 7.6% = 76.00; vNF = vProd
    assert t.find(f"{NFE}vProd").text == "1000.00"
    assert t.find(f"{NFE}vICMS").text == "120.00"
    assert t.find(f"{NFE}vPIS").text == "16.50"
    assert t.find(f"{NFE}vCOFINS").text == "76.00"
    assert t.find(f"{NFE}vNF").text == "1000.00"


def test_a_top_up_tax_percent_is_refused_with_the_por_dentro_explanation():
    doc = _doc(lines=[LineInput("x", Decimal("1"), Decimal("10"), Decimal("18"),
                                extra={"ncm": "84713012", "cfop": "5102", "p_icms": "18"})])
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(doc)
    assert any("por dentro" in p["message"] for p in exc.value.problems)


def test_simples_nacional_uses_csosn(a1):
    doc = _doc(seller=_seller(crt="1", default_icms_situacao="102", default_pis_cst="49", default_cofins_cst="49"))
    xml = _signed(doc)
    assert FMT.schema_errors(xml) == []
    assert _f(xml, "infNFe/det/imposto/ICMS/ICMSSN102/CSOSN").text == "102"
    with pytest.raises(EInvoiceDataMissing):  # a CST under Simples is refused
        FMT.build(_doc(seller=_seller(crt="1"), lines=[_line(icms_situacao="00")]))


def test_exempt_icms_and_non_taxed_pis(a1):
    xml = _signed(_doc(lines=[_line(icms_situacao="40", pis_cst="07", cofins_cst="07")]))
    assert FMT.schema_errors(xml) == []
    assert _f(xml, "infNFe/det/imposto/ICMS/ICMS40/CST").text == "40"
    assert _f(xml, "infNFe/det/imposto/PIS/PISNT/CST").text == "07"


def test_final_consumer_with_cpf_in_the_same_state(a1):
    doc = _doc(buyer=_buyer(tax_id="52998224725", name="Joao da Silva", region="SP",
                            extra={"ind_ie_dest": "9", "bairro": "Moema", "codigo_municipio": "3550308"}))
    xml = _signed(doc)
    assert FMT.schema_errors(xml) == []
    assert _f(xml, "infNFe/dest/CPF").text == "52998224725"
    assert _f(xml, "infNFe/ide/indFinal").text == "1"
    assert _f(xml, "infNFe/ide/idDest").text == "1"


def test_foreign_buyer(a1):
    doc = _doc(buyer=PartyInput(name="ACME Inc", street="Main St", city="Miami", country_code="US",
                                extra={"codigo_pais_bacen": "2496", "id_estrangeiro": "98-7654321"}),
               lines=[_line(cfop="7102")])
    xml = _signed(doc)
    assert FMT.schema_errors(xml) == []
    assert _f(xml, "infNFe/dest/enderDest/UF").text == "EX"
    assert _f(xml, "infNFe/ide/idDest").text == "3"


def test_homologacao_forces_the_sefaz_test_recipient_name(a1):
    xml = _signed(_doc(seller=_seller(ambiente="2")))
    assert FMT.schema_errors(xml) == []
    assert _f(xml, "infNFe/ide/tpAmb").text == "2"
    assert _f(xml, "infNFe/dest/xNome").text == "NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL"


def test_devolucao_references_the_original_key(a1):
    with pytest.raises(EInvoiceDataMissing):
        FMT.build(_doc(is_credit_note=True))
    original = "35260911222333000181550010000001221000000017"
    xml = _signed(_doc(is_credit_note=True, extra={"original_reference": original},
                       lines=[_line(cfop="2202")]))
    assert FMT.schema_errors(xml) == []
    assert _f(xml, "infNFe/ide/finNFe").text == "4"
    assert _f(xml, "infNFe/ide/tpNF").text == "0"
    assert _f(xml, "infNFe/ide/NFref/refNFe").text == original


def test_missing_line_classification_is_reported():
    doc = _doc(lines=[LineInput("x", Decimal("1"), Decimal("10"), Decimal("0"))])
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(doc)
    assert {"ncm", "cfop"} <= {p["key"] for p in exc.value.problems}


def test_tampered_document_fails_signature_verification(a1):
    xml = _signed(_doc())
    assert not verify_signature(xml.replace("<vProd>1000.00</vProd>", "<vProd>1.00</vProd>", 1))


def test_schema_check_is_real(a1):
    xml = _signed(_doc())
    assert FMT.schema_errors(xml.replace("<NCM>84713012</NCM>", "<NCM>847130</NCM>"))


def test_missing_certificate_is_a_preflight_problem(monkeypatch):
    monkeypatch.delenv("NFE_PFX_PATH", raising=False)
    monkeypatch.delenv("NFE_PRIVATE_KEY_PATH", raising=False)
    assert FMT.signing_problems(_doc())[0]["key"] == "certificate"


def test_unconfigured_gateway_refuses(monkeypatch):
    monkeypatch.delenv("NFE_BASE_URL", raising=False)
    with pytest.raises(TransportNotConfigured):
        FMT.submit("<x/>", _doc())
