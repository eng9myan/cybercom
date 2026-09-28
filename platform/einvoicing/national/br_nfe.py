"""
Brazil -- NF-e 4.00, modelo 55 (B2B goods), signed with the issuer's
ICP-Brasil certificate and authorised by the state SEFAZ.

Built against the SEFAZ schema package (PL_010 v1.30, incl. the 2026 tax-
reform groups) vendored under schemas/br/. Scope and deliberate choices:

- ICMS, PIS and COFINS are *por dentro* in Brazil (embedded in the price;
  vNF = vProd). CyCom's generic lines add tax on top, so a Brazilian line
  must be posted with tax_percent = 0 and carry its ICMS situation and
  rate in national line fields instead. That's enforced (a line with a
  top-up tax_percent is refused with that explanation) so the NF-e total
  and the ledger total can never silently disagree.
- Tax regimes: Simples Nacional / MEI (CRT 1/4: CSOSN 102/103/300/400) and
  Regime Normal (CRT 3: ICMS CST 00 / 40 / 41 / 50); PIS/COFINS CST 01/02
  (alíquota), 04-09 (não tributado) and 49/99 (outras). ICMS-ST, IPI,
  DIFAL and the optional 2026 IBS/CBS test groups are not emitted -- a
  line needing them is outside what this builder claims to support.
- nNF is the engine's gap-free per-tenant sequence; the chave de acesso is
  computed with its mod-11 check digit; cNF is derived from the document
  UUID (random-looking, never equal to nNF).
- Signature: XMLDSig enveloped over infNFe, RSA-SHA1 + C14N 1.0 exactly as
  the NF-e manual mandates (implemented directly -- general XMLDSig
  libraries now refuse SHA-1). Certificate: NFE_PFX_PATH + NFE_PFX_PASSWORD
  (the usual A1 .pfx) or NFE_PRIVATE_KEY_PATH / NFE_CERT_PATH.
- tpAmb=2 (homologação) forces the recipient name SEFAZ requires for
  test documents.
- NFS-e (services), NFC-e (modelo 65) and the SEFAZ SOAP/mTLS transport
  itself are out of scope here; transmission goes through NFE_BASE_URL /
  NFE_API_KEY (an authorisation gateway).
"""
from __future__ import annotations

import base64
import hashlib
import os
import re
from datetime import timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

from lxml import etree as ET

from .base import (
    DocInput,
    EInvoiceDataMissing,
    FieldSpec,
    NationalFormat,
    TransportNotConfigured,
    fmt,
    resolve_line_value,
)
from .transport import IntermediaryClient

NS = "http://www.portalfiscal.inf.br/nfe"
DS = "http://www.w3.org/2000/09/xmldsig#"
C14N = "http://www.w3.org/TR/2001/REC-xml-c14n-20010315"

UF_IBGE = {
    "RO": "11", "AC": "12", "AM": "13", "RR": "14", "PA": "15", "AP": "16", "TO": "17", "MA": "21",
    "PI": "22", "CE": "23", "RN": "24", "PB": "25", "PE": "26", "AL": "27", "SE": "28", "BA": "29",
    "MG": "31", "ES": "32", "RJ": "33", "SP": "35", "PR": "41", "SC": "42", "RS": "43", "MS": "50",
    "MT": "51", "GO": "52", "DF": "53",
}
UF_CHOICES = tuple((uf, uf) for uf in sorted(UF_IBGE))
CRT = (("1", "1 Simples Nacional"), ("2", "2 Simples Nacional - excesso sublimite"),
       ("3", "3 Regime Normal"), ("4", "4 MEI"))
ICMS_SITUACAO = (
    ("00", "CST 00 - tributada integralmente"), ("40", "CST 40 - isenta"),
    ("41", "CST 41 - não tributada"), ("50", "CST 50 - suspensão"),
    ("102", "CSOSN 102 - Simples sem crédito"), ("103", "CSOSN 103 - isenção faixa de receita"),
    ("300", "CSOSN 300 - imune"), ("400", "CSOSN 400 - não tributada pelo Simples"),
)
_CST_NORMAL = {"00", "40", "41", "50"}
_CSOSN = {"102", "103", "300", "400"}
PIS_COFINS_CST = tuple((c, c) for c in ("01", "02", "04", "05", "06", "07", "08", "09", "49", "99"))
ORIGEM = tuple((str(i), str(i)) for i in range(9))
IND_IE = (("1", "1 Contribuinte ICMS"), ("2", "2 Contribuinte isento"), ("9", "9 Não contribuinte"))
IND_PRES = (("0", "0 Não se aplica"), ("1", "1 Presencial"), ("2", "2 Internet"),
            ("3", "3 Teleatendimento"), ("4", "4 Entrega em domicílio"), ("9", "9 Outros"))
FORMA_PAG = (("01", "01 Dinheiro"), ("03", "03 Cartão de crédito"), ("04", "04 Cartão de débito"),
             ("15", "15 Boleto"), ("17", "17 PIX"), ("18", "18 Transferência"), ("90", "90 Sem pagamento"),
             ("99", "99 Outros"))

_is_br = lambda doc, p: (p.country_code or "").upper() == "BR"  # noqa: E731
_foreign = lambda doc, p: bool(p.country_code) and not _is_br(doc, p)  # noqa: E731


def _aliquota_cst(key):
    return lambda doc, line: (resolve_line_value(
        next(f for f in BrNfe.fields if f.key == key), doc, line) or "") in ("01", "02")


def _dv(digits: str, weights) -> int:
    vals = [ord(c) - 48 for c in digits]
    s = sum(v * w for v, w in zip(vals, weights))
    r = s % 11
    return 0 if r < 2 else 11 - r


def cnpj_valid(cnpj: str) -> bool:
    c = re.sub(r"[^0-9A-Z]", "", (cnpj or "").upper())
    if not re.fullmatch(r"[0-9A-Z]{12}[0-9]{2}", c) or len(set(c)) == 1:
        return False
    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    w2 = [6] + w1
    return _dv(c[:12], w1) == int(c[12]) and _dv(c[:13], w2) == int(c[13])


def cpf_valid(cpf: str) -> bool:
    c = re.sub(r"\D", "", cpf or "")
    if len(c) != 11 or len(set(c)) == 1:
        return False
    return (_dv(c[:9], range(10, 1, -1)) == int(c[9])
            and _dv(c[:10], range(11, 1, -1)) == int(c[10]))


def chave_dv(chave43: str) -> int:
    """Mod-11, weights 2..9 from the right. Characters are valued ord(c)-48,
    which is the digit itself for 0-9 and the NT 2025 rule for the letters
    of an alphanumeric CNPJ."""
    weights = [2, 3, 4, 5, 6, 7, 8, 9]
    s = sum((ord(c) - 48) * weights[i % 8] for i, c in enumerate(reversed(chave43)))
    r = s % 11
    return 0 if r in (0, 1) else 11 - r


class BrNfe(NationalFormat):
    mode = "br_nfe"
    label = "Brazil - NF-e 4.00 (modelo 55)"
    countries = ("BR",)
    xsd = "br/nfe_v4.00.xsd"
    fields = [
        FieldSpec("seller", "tax_id", "CNPJ", pattern=r"[0-9A-Z]{12}[0-9]{2}"),
        FieldSpec("seller", "name", "Razão social (xNome)"),
        FieldSpec("seller", "ie", "Inscrição estadual", pattern=r"[0-9]{2,14}|ISENTO"),
        FieldSpec("seller", "crt", "Regime tributário (CRT)", choices=CRT),
        FieldSpec("seller", "street", "Logradouro"),
        FieldSpec("seller", "building_number", "Número", required=False, help="Blank is sent as 'S/N'."),
        FieldSpec("seller", "bairro", "Bairro"),
        FieldSpec("seller", "city", "Município"),
        FieldSpec("seller", "codigo_municipio", "Código do município (IBGE)", pattern=r"\d{7}"),
        FieldSpec("seller", "region", "UF", choices=UF_CHOICES),
        FieldSpec("seller", "postal_code", "CEP", pattern=r"\d{8}"),
        FieldSpec("seller", "serie", "Série da NF-e", pattern=r"0|[1-9][0-9]{0,2}"),
        FieldSpec("seller", "natureza_operacao", "Natureza da operação (natOp)",
                  help="e.g. 'Venda de mercadoria'."),
        FieldSpec("seller", "ambiente", "Ambiente (tpAmb)", choices=(("1", "1 Produção"), ("2", "2 Homologação"))),
        FieldSpec("seller", "ind_pres", "Indicador de presença (indPres)", choices=IND_PRES),
        FieldSpec("seller", "forma_pagamento", "Meio de pagamento (tPag)", choices=FORMA_PAG),
        FieldSpec("seller", "utc_offset", "Fuso horário", required=False, pattern=r"[+-](0[0-9]|1[0-4]):[0-5][0-9]",
                  help="Offset of dhEmi; defaults to -03:00 (Brasília)."),
        FieldSpec("seller", "default_origem", "Origem da mercadoria (default)", choices=ORIGEM,
                  help="0 = nacional."),
        FieldSpec("seller", "default_icms_situacao", "ICMS CST/CSOSN (default)", required=False, choices=ICMS_SITUACAO),
        FieldSpec("seller", "default_pis_cst", "PIS CST (default)", required=False, choices=PIS_COFINS_CST),
        FieldSpec("seller", "default_cofins_cst", "COFINS CST (default)", required=False, choices=PIS_COFINS_CST),
        FieldSpec("seller", "default_p_pis", "Alíquota PIS % (default)", required=False, pattern=r"\d{1,3}(\.\d{1,4})?"),
        FieldSpec("seller", "default_p_cofins", "Alíquota COFINS % (default)", required=False,
                  pattern=r"\d{1,3}(\.\d{1,4})?"),
        FieldSpec("buyer", "name", "Destinatário (xNome)"),
        FieldSpec("buyer", "country_code", "País", pattern=r"[A-Z]{2}"),
        FieldSpec("buyer", "tax_id", "CNPJ / CPF", pattern=r"[0-9A-Z]{12}[0-9]{2}|[0-9]{11}", when=_is_br),
        FieldSpec("buyer", "ind_ie_dest", "Indicador IE do destinatário", choices=IND_IE, when=_is_br),
        FieldSpec("buyer", "ie", "Inscrição estadual do destinatário", pattern=r"[0-9]{2,14}",
                  when=lambda doc, p: _is_br(doc, p) and p.get("ind_ie_dest") == "1"),
        FieldSpec("buyer", "street", "Logradouro"),
        FieldSpec("buyer", "bairro", "Bairro", when=_is_br),
        FieldSpec("buyer", "city", "Município"),
        FieldSpec("buyer", "codigo_municipio", "Código do município (IBGE)", pattern=r"\d{7}", when=_is_br),
        FieldSpec("buyer", "region", "UF", choices=UF_CHOICES, when=_is_br),
        FieldSpec("buyer", "postal_code", "CEP", pattern=r"\d{8}", when=_is_br),
        FieldSpec("buyer", "id_estrangeiro", "Identificação do estrangeiro", required=False, when=_foreign),
        FieldSpec("buyer", "codigo_pais_bacen", "Código do país (BACEN)", pattern=r"\d{1,4}", when=_foreign),
        FieldSpec("line", "ncm", "NCM", pattern=r"\d{8}"),
        FieldSpec("line", "cfop", "CFOP", pattern=r"[1235-7]\d{3}"),
        FieldSpec("line", "origem", "Origem", choices=ORIGEM, default_from="default_origem"),
        FieldSpec("line", "icms_situacao", "ICMS CST / CSOSN", choices=ICMS_SITUACAO,
                  default_from="default_icms_situacao"),
        FieldSpec("line", "p_icms", "Alíquota ICMS %", pattern=r"\d{1,3}(\.\d{1,4})?",
                  when=lambda doc, line: resolve_line_value(
                      next(f for f in BrNfe.fields if f.key == "icms_situacao"), doc, line) == "00"),
        FieldSpec("line", "pis_cst", "PIS CST", choices=PIS_COFINS_CST, default_from="default_pis_cst"),
        FieldSpec("line", "cofins_cst", "COFINS CST", choices=PIS_COFINS_CST, default_from="default_cofins_cst"),
        FieldSpec("line", "p_pis", "Alíquota PIS %", pattern=r"\d{1,3}(\.\d{1,4})?", default_from="default_p_pis",
                  when=_aliquota_cst("pis_cst")),
        FieldSpec("line", "p_cofins", "Alíquota COFINS %", pattern=r"\d{1,3}(\.\d{1,4})?",
                  default_from="default_p_cofins", when=_aliquota_cst("cofins_cst")),
        FieldSpec("line", "unit", "Unidade comercial", required=False),
        FieldSpec("document", "mod_frete", "Modalidade do frete", required=False,
                  choices=(("0", "0 CIF"), ("1", "1 FOB"), ("2", "2 Terceiros"), ("9", "9 Sem frete"))),
    ]

    def _v(self, key, doc, line):
        return resolve_line_value(next(f for f in self.fields if f.key == key), doc, line)

    def validate(self, doc: DocInput) -> None:
        problems: list[dict] = []
        try:
            super().validate(doc)
        except EInvoiceDataMissing as exc:
            problems = exc.problems
        if doc.seller.tax_id and not cnpj_valid(doc.seller.tax_id):
            problems.append({"scope": "seller", "key": "tax_id", "label": "CNPJ", "message": "check digits are invalid"})
        bt = re.sub(r"[^0-9A-Z]", "", (doc.buyer.tax_id or "").upper())
        if _is_br(doc, doc.buyer) and bt and not (cnpj_valid(bt) if len(bt) == 14 else cpf_valid(bt)):
            problems.append({"scope": "buyer", "key": "tax_id", "label": "CNPJ / CPF",
                             "message": "check digits are invalid"})
        simples = doc.seller.get("crt") in ("1", "2", "4")
        for i, line in enumerate(doc.lines, start=1):
            if Decimal(line.tax_percent) != 0:
                problems.append({"scope": f"line[{i}]", "key": "tax_percent", "label": "Imposto",
                                 "message": "Brazilian ICMS/PIS/COFINS are included in the price (por dentro): "
                                            "post the line with 0% and set its ICMS/PIS/COFINS fields instead"})
            sit = self._v("icms_situacao", doc, line)
            if sit and doc.seller.get("crt"):
                if simples and sit not in _CSOSN:
                    problems.append({"scope": f"line[{i}]", "key": "icms_situacao", "label": "ICMS",
                                     "message": "a Simples Nacional issuer uses a CSOSN (102/103/300/400)"})
                if not simples and sit not in _CST_NORMAL:
                    problems.append({"scope": f"line[{i}]", "key": "icms_situacao", "label": "ICMS",
                                     "message": "a Regime Normal issuer uses an ICMS CST (00/40/41/50)"})
        if doc.is_credit_note and not re.fullmatch(r"\d{44}", (doc.get("original_reference") or "").strip()):
            problems.append({"scope": "document", "key": "original_reference", "label": "Chave da NF-e referenciada",
                             "message": "a devolução must reference the original NF-e's 44-digit access key"})
        if problems:
            raise EInvoiceDataMissing(self.mode, problems)

    def signing_status(self) -> bool:
        try:
            _load_certificate()
            return True
        except TransportNotConfigured:
            return False

    def signing_problems(self, doc: DocInput) -> list[dict]:
        try:
            _load_certificate()
        except TransportNotConfigured as exc:
            return [{"scope": "seller", "key": "certificate", "label": "Certificado digital ICP-Brasil (A1)",
                     "message": str(exc)}]
        return []

    # -- chave ----------------------------------------------------------------------
    def chave(self, doc: DocInput) -> str:
        uf = UF_IBGE[doc.seller.region.upper()]
        aamm = doc.issue_dt.strftime("%y%m")
        cnpj = re.sub(r"[^0-9A-Z]", "", doc.seller.tax_id.upper())
        serie = f"{int(doc.seller.get('serie')):03d}"
        nnf = f"{int(doc.icv):09d}"
        cnf = self._cnf(doc)
        base = f"{uf}{aamm}{cnpj}55{serie}{nnf}1{cnf}"
        return base + str(chave_dv(base))

    @staticmethod
    def _cnf(doc: DocInput) -> str:
        h = int(hashlib.sha256((doc.uuid or doc.number).encode()).hexdigest(), 16) % 10**8
        cnf = f"{h:08d}"
        return cnf if cnf != f"{int(doc.icv):08d}"[-8:] else f"{(h + 1) % 10**8:08d}"

    # -- build ------------------------------------------------------------------------
    def build(self, doc: DocInput) -> str:
        self.validate(doc)
        chave = self.chave(doc)
        homolog = doc.seller.get("ambiente") == "2"
        simples = doc.seller.get("crt") in ("1", "2", "4")
        buyer_br = _is_br(doc, doc.buyer)
        seller_uf = doc.seller.region.upper()

        nfe = ET.Element(f"{{{NS}}}NFe", nsmap={None: NS})
        inf = _e(nfe, "infNFe")
        inf.set("versao", "4.00")
        inf.set("Id", f"NFe{chave}")

        ide = _e(inf, "ide")
        _t(ide, "cUF", UF_IBGE[seller_uf])
        _t(ide, "cNF", chave[35:43])
        _t(ide, "natOp", _s(doc.seller.get("natureza_operacao"), 60))
        _t(ide, "mod", "55")
        _t(ide, "serie", str(int(doc.seller.get("serie"))))
        _t(ide, "nNF", str(int(doc.icv)))
        _t(ide, "dhEmi", _dh(doc))
        _t(ide, "tpNF", "0" if doc.is_credit_note else "1")
        if not buyer_br:
            id_dest = "3"
        else:
            id_dest = "1" if (doc.buyer.region or "").upper() == seller_uf else "2"
        _t(ide, "idDest", id_dest)
        _t(ide, "cMunFG", doc.seller.get("codigo_municipio"))
        _t(ide, "tpImp", "1")
        _t(ide, "tpEmis", "1")
        _t(ide, "cDV", chave[-1])
        _t(ide, "tpAmb", "2" if homolog else "1")
        _t(ide, "finNFe", "4" if doc.is_credit_note else "1")
        ind_final = "1" if (buyer_br and doc.buyer.get("ind_ie_dest") == "9") else "0"
        _t(ide, "indFinal", ind_final)
        _t(ide, "indPres", doc.seller.get("ind_pres"))
        _t(ide, "procEmi", "0")
        _t(ide, "verProc", "CyCom ERP 1.0")
        if doc.is_credit_note:
            _t(_e(ide, "NFref"), "refNFe", doc.get("original_reference").strip())

        emit = _e(inf, "emit")
        _t(emit, "CNPJ", re.sub(r"[^0-9A-Z]", "", doc.seller.tax_id.upper()))
        _t(emit, "xNome", _s(doc.seller.name, 60))
        ender = _e(emit, "enderEmit")
        _t(ender, "xLgr", _s(doc.seller.street, 60))
        _t(ender, "nro", _s(doc.seller.building_number or "S/N", 60))
        _t(ender, "xBairro", _s(doc.seller.get("bairro"), 60))
        _t(ender, "cMun", doc.seller.get("codigo_municipio"))
        _t(ender, "xMun", _s(doc.seller.city, 60))
        _t(ender, "UF", seller_uf)
        _t(ender, "CEP", doc.seller.postal_code)
        _t(ender, "cPais", "1058")
        _t(ender, "xPais", "Brasil")
        _t(emit, "IE", doc.seller.get("ie"))
        _t(emit, "CRT", doc.seller.get("crt"))

        dest = _e(inf, "dest")
        bt = re.sub(r"[^0-9A-Z]", "", (doc.buyer.tax_id or "").upper())
        if buyer_br:
            _t(dest, "CNPJ" if len(bt) == 14 else "CPF", bt)
        else:
            # always present for a foreign buyer; may legitimately be empty
            _e(dest, "idEstrangeiro").text = _s(doc.buyer.get("id_estrangeiro") or "", 20) or None
        _t(dest, "xNome", "NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL" if homolog
           else _s(doc.buyer.name, 60))
        ed = _e(dest, "enderDest")
        _t(ed, "xLgr", _s(doc.buyer.street, 60))
        _t(ed, "nro", _s(doc.buyer.building_number or "S/N", 60))
        _t(ed, "xBairro", _s(doc.buyer.get("bairro") or ("EXTERIOR" if not buyer_br else ""), 60))
        _t(ed, "cMun", doc.buyer.get("codigo_municipio") if buyer_br else "9999999")
        _t(ed, "xMun", _s(doc.buyer.city, 60) if buyer_br else "EXTERIOR")
        _t(ed, "UF", doc.buyer.region.upper() if buyer_br else "EX")
        if buyer_br:
            _t(ed, "CEP", doc.buyer.postal_code)
            _t(ed, "cPais", "1058")
            _t(ed, "xPais", "Brasil")
        else:
            _t(ed, "cPais", doc.buyer.get("codigo_pais_bacen"))
        _t(dest, "indIEDest", doc.buyer.get("ind_ie_dest") if buyer_br else "9")
        if buyer_br and doc.buyer.get("ind_ie_dest") == "1":
            _t(dest, "IE", doc.buyer.get("ie"))
        if doc.buyer.email:
            _t(dest, "email", _s(doc.buyer.email, 60))

        tot = {k: Decimal("0") for k in ("vBC", "vICMS", "vProd", "vPIS", "vCOFINS")}
        for i, line in enumerate(doc.lines, start=1):
            det = _e(inf, "det")
            det.set("nItem", str(i))
            prod = _e(det, "prod")
            vprod = line.net
            tot["vProd"] += vprod
            _t(prod, "cProd", _s(line.get("sku") or str(i), 60))
            _t(prod, "cEAN", "SEM GTIN")
            _t(prod, "xProd", _s(line.name, 120) or "-")
            _t(prod, "NCM", self._v("ncm", doc, line))
            _t(prod, "CFOP", self._v("cfop", doc, line))
            unit = _s(line.get("unit") or "UN", 6)
            _t(prod, "uCom", unit)
            _t(prod, "qCom", _dec(line.quantity, 4))
            _t(prod, "vUnCom", _dec(line.unit_price, 10))
            _t(prod, "vProd", fmt(vprod, 2))
            _t(prod, "cEANTrib", "SEM GTIN")
            _t(prod, "uTrib", unit)
            _t(prod, "qTrib", _dec(line.quantity, 4))
            _t(prod, "vUnTrib", _dec(line.unit_price, 10))
            _t(prod, "indTot", "1")

            imp = _e(det, "imposto")
            icms = _e(imp, "ICMS")
            sit = self._v("icms_situacao", doc, line)
            orig = self._v("origem", doc, line)
            if simples:
                g = _e(icms, "ICMSSN102")
                _t(g, "orig", orig)
                _t(g, "CSOSN", sit)
            elif sit == "00":
                p = Decimal(str(self._v("p_icms", doc, line)))
                v = (vprod * p / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
                tot["vBC"] += vprod
                tot["vICMS"] += v
                g = _e(icms, "ICMS00")
                _t(g, "orig", orig)
                _t(g, "CST", "00")
                _t(g, "modBC", "3")
                _t(g, "vBC", fmt(vprod, 2))
                _t(g, "pICMS", _rate(p))
                _t(g, "vICMS", fmt(v, 2))
            else:
                g = _e(icms, "ICMS40")
                _t(g, "orig", orig)
                _t(g, "CST", sit)
            for tax, key in (("PIS", "pis"), ("COFINS", "cofins")):
                cst = self._v(f"{key}_cst", doc, line)
                wrap = _e(imp, tax)
                if cst in ("01", "02"):
                    p = Decimal(str(self._v(f"p_{key}", doc, line)))
                    v = (vprod * p / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
                    tot[f"v{tax}"] += v
                    g = _e(wrap, f"{tax}Aliq")
                    _t(g, "CST", cst)
                    _t(g, "vBC", fmt(vprod, 2))
                    _t(g, f"p{tax}", _rate(p))
                    _t(g, f"v{tax}", fmt(v, 2))
                elif cst in ("04", "05", "06", "07", "08", "09"):
                    _t(_e(wrap, f"{tax}NT"), "CST", cst)
                else:
                    g = _e(wrap, f"{tax}Outr")
                    _t(g, "CST", cst)
                    _t(g, "vBC", "0.00")
                    _t(g, f"p{tax}", "0.00")
                    _t(g, f"v{tax}", "0.00")

        total = _e(_e(inf, "total"), "ICMSTot")
        for k in ("vBC", "vICMS"):
            _t(total, k, fmt(tot[k], 2))
        for k in ("vICMSDeson", "vFCP", "vBCST", "vST", "vFCPST", "vFCPSTRet"):
            _t(total, k, "0.00")
        _t(total, "vProd", fmt(tot["vProd"], 2))
        for k in ("vFrete", "vSeg", "vDesc", "vII", "vIPI", "vIPIDevol"):
            _t(total, k, "0.00")
        _t(total, "vPIS", fmt(tot["vPIS"], 2))
        _t(total, "vCOFINS", fmt(tot["vCOFINS"], 2))
        _t(total, "vOutro", "0.00")
        _t(total, "vNF", fmt(tot["vProd"], 2))  # por dentro: taxes are inside vProd

        _t(_e(inf, "transp"), "modFrete", doc.get("mod_frete") or "9")

        pag = _e(inf, "pag")
        dp = _e(pag, "detPag")
        if doc.is_credit_note:
            _t(dp, "tPag", "90")
            _t(dp, "vPag", "0.00")
        else:
            _t(dp, "tPag", doc.seller.get("forma_pagamento"))
            _t(dp, "vPag", fmt(tot["vProd"], 2))

        return '<?xml version="1.0" encoding="UTF-8"?>' + ET.tostring(nfe, encoding="unicode")

    # -- signature --------------------------------------------------------------------
    def sign(self, document: str, doc: DocInput) -> str:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import Encoding

        key, cert = _load_certificate()
        root = ET.fromstring(document.encode("utf-8"))
        inf = root.find(f"{{{NS}}}infNFe")
        ref_id = inf.get("Id")
        digest = base64.b64encode(hashlib.sha1(ET.tostring(inf, method="c14n")).digest()).decode()

        sig = ET.SubElement(root, f"{{{DS}}}Signature", nsmap={None: DS})
        si = ET.SubElement(sig, f"{{{DS}}}SignedInfo")
        ET.SubElement(si, f"{{{DS}}}CanonicalizationMethod").set("Algorithm", C14N)
        ET.SubElement(si, f"{{{DS}}}SignatureMethod").set("Algorithm", "http://www.w3.org/2000/09/xmldsig#rsa-sha1")
        ref = ET.SubElement(si, f"{{{DS}}}Reference")
        ref.set("URI", f"#{ref_id}")
        tr = ET.SubElement(ref, f"{{{DS}}}Transforms")
        ET.SubElement(tr, f"{{{DS}}}Transform").set("Algorithm", "http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        ET.SubElement(tr, f"{{{DS}}}Transform").set("Algorithm", C14N)
        ET.SubElement(ref, f"{{{DS}}}DigestMethod").set("Algorithm", "http://www.w3.org/2000/09/xmldsig#sha1")
        ET.SubElement(ref, f"{{{DS}}}DigestValue").text = digest

        signed_info = ET.tostring(si, method="c14n")
        value = key.sign(signed_info, padding.PKCS1v15(), hashes.SHA1())  # noqa: S303 - mandated by NF-e
        ET.SubElement(sig, f"{{{DS}}}SignatureValue").text = base64.b64encode(value).decode()
        x509data = ET.SubElement(ET.SubElement(sig, f"{{{DS}}}KeyInfo"), f"{{{DS}}}X509Data")
        ET.SubElement(x509data, f"{{{DS}}}X509Certificate").text = base64.b64encode(
            cert.public_bytes(Encoding.DER)).decode()
        return '<?xml version="1.0" encoding="UTF-8"?>' + ET.tostring(root, encoding="unicode")

    def filename(self, doc: DocInput) -> str:
        return f"{self.chave(doc)}-nfe.xml"

    def client(self):
        return IntermediaryClient("NFE", channel_label="NF-e authorisation gateway (SEFAZ)")


def verify_signature(signed_xml: str) -> bool:
    """Recompute digest + RSA-SHA1 check against the embedded certificate."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    root = ET.fromstring(signed_xml.encode("utf-8"))
    sig = root.find(f"{{{DS}}}Signature")
    inf = root.find(f"{{{NS}}}infNFe")
    digest = base64.b64encode(hashlib.sha1(ET.tostring(inf, method="c14n")).digest()).decode()
    if digest != sig.find(f".//{{{DS}}}DigestValue").text:
        return False
    cert = x509.load_der_x509_certificate(base64.b64decode(sig.find(f".//{{{DS}}}X509Certificate").text))
    try:
        cert.public_key().verify(base64.b64decode(sig.find(f"{{{DS}}}SignatureValue").text),
                                 ET.tostring(sig.find(f"{{{DS}}}SignedInfo"), method="c14n"),
                                 padding.PKCS1v15(), hashes.SHA1())  # noqa: S303
        return True
    except Exception:
        return False


def _load_certificate():
    from cryptography import x509
    from cryptography.hazmat.primitives.serialization import load_der_private_key, load_pem_private_key
    from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates

    from ..signing import KEY_LOADER

    pfx_path = os.getenv("NFE_PFX_PATH", "")
    if pfx_path and os.path.exists(pfx_path):
        with open(pfx_path, "rb") as fh:
            try:
                key, cert, _ = load_key_and_certificates(fh.read(), os.getenv("NFE_PFX_PASSWORD", "").encode() or None)
            except ValueError as exc:
                raise TransportNotConfigured(f"The A1 certificate (.pfx) could not be opened: {exc}") from exc
        return key, cert
    key_bytes, cert_bytes = KEY_LOADER("br_nfe")
    if not key_bytes or not cert_bytes:
        raise TransportNotConfigured("No ICP-Brasil A1 certificate installed. Set NFE_PFX_PATH (+ NFE_PFX_PASSWORD) "
                                     "or NFE_PRIVATE_KEY_PATH / NFE_CERT_PATH.")
    password = os.getenv("NFE_KEY_PASSWORD", "").encode() or None
    try:
        key = (load_pem_private_key(key_bytes, password) if b"-----BEGIN" in key_bytes
               else load_der_private_key(key_bytes, password))
        cert = (x509.load_pem_x509_certificate(cert_bytes) if b"-----BEGIN" in cert_bytes
                else x509.load_der_x509_certificate(cert_bytes))
    except (ValueError, TypeError) as exc:
        raise TransportNotConfigured(f"The certificate could not be loaded: {exc}") from exc
    return key, cert


def _e(parent, tag):
    return ET.SubElement(parent, f"{{{NS}}}{tag}")


def _t(parent, tag, text):
    if text is None or text == "":
        return None
    el = ET.SubElement(parent, f"{{{NS}}}{tag}")
    el.text = str(text)
    return el


def _s(value, limit: int) -> str:
    """NF-e TString: Latin-1, no leading/trailing/double spaces."""
    text = "".join(ch if ord(ch) < 256 else "?" for ch in str(value or ""))
    return re.sub(r"\s+", " ", text).strip()[:limit].strip()


def _dh(doc: DocInput) -> str:
    offset = doc.seller.get("utc_offset") or "-03:00"
    sign = -1 if offset.startswith("-") else 1
    hh, mm = offset[1:].split(":")
    tz = timezone(sign * timedelta(hours=int(hh), minutes=int(mm)))
    dt = doc.issue_dt if doc.issue_dt.tzinfo else doc.issue_dt.replace(tzinfo=tz)
    return dt.astimezone(tz).replace(microsecond=0).isoformat()


def _dec(value, max_places: int) -> str:
    d = Decimal(str(value)).normalize()
    places = min(max_places, max(0, -d.as_tuple().exponent))
    return fmt(d, places) if places else str(int(d))


def _rate(p: Decimal) -> str:
    d = Decimal(str(p)).normalize()
    places = min(4, max(2, -d.as_tuple().exponent))
    return fmt(d, places)
