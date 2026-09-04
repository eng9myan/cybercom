# Spec — E-Invoicing Clearance Engine (ZATCA + JoFotara + Peppol)

> The #1 launch-critical build for KSA/JO tax invoices. Consolidates what already
> exists in the repo, what's still a stub, and the implementable plan. **Status:**
> draft for CDAC. Owner: Finance pod. Estimate: ~2–3 weeks eng + regulator
> conformance cycles (which are calendar-bound, not eng-bound).

---

## 1. What exists in the repo today (audited 2026-09-04)

| Piece | Location | State |
|---|---|---|
| Routing on invoice post | `cycom/products/cycom/ar_ap/compliance_client.py` `notify_invoice_finalized()` | **Real.** Non-blocking `httpx.post` to a gateway; region from `tenant.country_code` → jurisdiction. Tested (`test_compliance_routing.py`). |
| Compliance gateway (FastAPI microservice) | `cycom/compliance-gateway/` (`main.py`, `jordan_fotara.py`, `saudi_zatca.py`, `peppol_ubl.py`) | **Skeleton.** `process_fiscal_compliance()` switches JO/SA/US-EU-GB. Plugins build a payload + a QR **URL** and return `{"status": "certified"/"cleared"}` **without calling any real government API or signing anything.** `sign_ubl_xml` is a fake `digest[:32]`. |
| `JoFotaraClient` | `cymed/products/cymed/integrations/jofawtra/client.py` (325 lines) | **Real HTTP client.** `submit_invoice(ubl_xml, uuid)`, `check_status(ref)`, basic+bearer auth, `_sign_xml` XAdES hook (warns + submits unsigned if no key). Good sandbox-onboarding README. Does **not** build UBL. |
| `ZATCAClient` | `cymed/products/cymed/integrations/zakata/client.py` (131 lines) | **Real HTTP client.** `report_invoice(xml)`, `clear_invoice(xml)`, CSID token via `/compliance`. Uses `requests`. Does **not** build UBL, sign, or compute hash/QR. |
| Invoice model | `cycom/products/cycom/ar_ap/models.py` `Invoice` | **No e-invoice fields** — no `uuid`, `qr`, `hash`, `prev_hash`, `clearance_status`, `cleared_xml_ref`. Currency defaults `JOD`. |
| Jurisdiction / region map | `cycom/products/cycom/localization/` (`0002_seed_jurisdictions`) | **Real.** `jurisdiction.compliance_region`. |

**Summary:** the *plumbing* (routing, a gateway boundary, two authenticated API clients,
jurisdiction mapping) is real. The *conformance-grade core* (correct UBL 2.1, XAdES signing,
the ZATCA cryptographic stamp + QR + PIH chain, result persistence, real submission) is stub
or missing. This is the ~2–3 week build.

---

## 2. Target design

```
Invoice.post()  ──►  finance.einvoice.clear(invoice)          [synchronous, fail-closed for KSA;
                         │                                       async + non-blocking for JO until
                         │                                       JoFotara is mandatory for that tenant]
                         ▼
        ┌───────────  EInvoiceEngine  ───────────┐
        │  mode = mode_for(org.country, flavor)  │   sa_zatca | jo_jofotara | ae_peppol | none
        │  1. build canonical UBL 2.1 (per mode) │   ◄── UBL builder, per-mode
        │  2. compute PIH / prev-hash chain      │   ◄── per tenant+org+device sequence
        │  3. sign (XAdES-B / ZATCA CSR cert)    │   ◄── real signer (xmlsec / signxml + HSM/file key)
        │  4. render QR (TLV base64 / verify URL)│
        │  5. submit  (ZATCAClient / JoFotaraClient / Peppol AP)
        │  6. persist result on Invoice           │   uuid, hash, prev_hash, qr, status,
        │     + archive cleared XML → CyVault     │   cleared_xml_ref, cleared_at
        └────────────────────────────────────────┘
```

**Key decision: retire `compliance-gateway/`'s plugin stubs; the engine calls the real
`ZATCAClient` / `JoFotaraClient` directly** (promoted to `platform/einvoicing/`). Reasons:
the real clients already handle auth, retries, sandbox config, and have onboarding docs; the
gateway plugins are simpler reimplementations that would drift. Keep `compliance_client.py`'s
*routing* idea (region → mode) but call the engine in-process, not a separate microservice —
one less thing to deploy for launch. (A gateway can come back later if a non-Django consumer
needs it.)

---

## 3. Invoice model — M1 additive fields (per `canonical-data-model-v1.md` §6.1)

On `cycom/products/cycom/ar_ap/Invoice` (all nullable at M1):

```python
einvoice_mode        = models.CharField(max_length=16, blank=True)   # sa_zatca|jo_jofotara|ae_peppol
einvoice_uuid        = models.UUIDField(null=True, blank=True)
einvoice_icv         = models.PositiveBigIntegerField(null=True)      # invoice counter value (per seq)
einvoice_pih         = models.TextField(blank=True)                   # previous invoice hash (base64)
einvoice_hash        = models.TextField(blank=True)                   # this invoice hash
einvoice_qr          = models.TextField(blank=True)                   # base64 TLV (SA) or verify URL (JO)
einvoice_status      = models.CharField(max_length=16, default="none")# none|pending|cleared|reported|rejected
einvoice_response    = models.JSONField(default=dict, blank=True)     # last gateway/ZATCA/JoFotara raw
einvoice_cleared_ref = models.CharField(max_length=200, blank=True)   # CyVault object id for cleared XML
einvoice_cleared_at  = models.DateTimeField(null=True, blank=True)
```

`EInvoiceSequence` (new, `PlatformModel` per org+device): `next_icv`, `last_hash` — the
gap-free counter + hash chain source (`H` C4). Locked row on each clearance.

---

## 4. Work breakdown

### 4.1 UBL 2.1 builder — `platform/einvoicing/ubl.py` (the bulk of the eng work)

Build from a canonical Invoice + lines + org + partner + tax rules. Two profiles:

| Mode | Standard | Must include |
|---|---|---|
| `sa_zatca` | ZATCA UBL 2.1, `reporting:1.0` / `clearance` | ICV, UUID, PIH, seller VAT + CRN + address, buyer (B2B), per-line `cac:InvoiceLine` with `cac:TaxTotal`, `cac:AllowanceCharge`, document-level `cac:TaxSubtotal` per rate + category, `cac:LegalMonetaryTotal`, invoice type code (388/381/383), `cbc:DocumentCurrencyCode`, timestamps |
| `jo_jofotara` | UBL 2.1 customization `PINT-JO` (income = `388`) | seller TIN + activity code, buyer TIN (or "General Public"), per-line, tax summary, `cbc:CustomizationID`, currency `JOD`, ISTD invoice type |
| `ae_peppol` | Peppol BIS Billing 3.0 (PINT AE when published) | BIS 3.0 mandatory set; route via a Peppol Access Point |

Validate every generated doc against the official XSD + Schematron (ZATCA publishes both;
ISTD publishes PINT-JO rules). Ship the schemas in `platform/einvoicing/schemas/`. A doc that
fails Schematron never gets submitted.

### 4.2 Hashing + QR

- **SA:** `hash = base64(sha256(canonicalized_xml))`; `PIH` = previous invoice's hash (seed
  `0` for the first). QR = base64 **TLV** of 9 tags (seller name, VAT, timestamp, total,
  VAT total, XML hash, ECDSA signature, public key, stamp signature) — tags 6–9 only after
  signing.
- **JO:** QR = the ISTD verify URL with TIN + invoice no + amount + a UUID; ISTD is moving
  toward a signed payload — follow the current PINT-JO QR rule at build time.

### 4.3 Signing — `platform/einvoicing/signing.py`

- **SA:** onboard a **CSID** (compliance CSR → ZATCA `/compliance` → binary security token +
  secret; then production CSID). Sign the XML invoice hash with the CSID private key (ECDSA
  secp256k1), embed `cac:Signature` + `ext:UBLExtensions` per ZATCA. Key in KMS/HSM, never a file in prod.
- **JO:** XAdES-B enveloped signature with the taxpayer cert (ISTD issues a test cert on
  sandbox onboarding). Wire `signxml` or `xmlsec` into `JoFotaraClient._sign_xml`.
- Test path: `EINVOICE_ALLOW_UNSIGNED=1` (sandbox only) — the clients already warn-and-continue.

### 4.4 Submission + result handling — `platform/einvoicing/engine.py`

- `EInvoiceEngine.clear(invoice)` → build → validate → chain → sign → submit → parse →
  persist → archive cleared XML to CyVault.
- **SA B2B = clearance** (blocking, invoice not valid until cleared); **SA B2C simplified =
  reporting** (within 24h, async). **JO = submit + poll** to `cleared`.
- Failure: `einvoice_status="rejected"`, store the reason, surface in the UI, **do not** roll
  back the GL entry (`compliance_client.py`'s existing principle) — but for SA B2B, block
  sending the invoice to the customer until cleared.
- Idempotent on `einvoice_uuid`; retry with backoff; DLQ after N.

### 4.5 Config / onboarding

Per-tenant `Integration` rows (`type="fatoora"` / `"jofotara"`), credentials in the vault:
- SA: `ZATCA_CSID`, `ZATCA_SECRET`, cert, `ZATCA_ENV` (sandbox/simulation/production)
- JO: `JOFOTARA_CLIENT_ID/SECRET`, `JOFOTARA_TAX_ID`, `JOFOTARA_ACTIVITY_CODE`, cert
Provisioning refuses to activate a flavor in SA/JO without the pack `ready` + credentials present
(`F.5`).

### 4.6 Tests (per `H` Q3 / `P`)

- UBL builder: golden-file tests vs ZATCA/ISTD sample invoices; XSD + Schematron pass.
- Hash chain: property test — chain unbroken across N invoices, gap-free ICV (`H` C4/Q8).
- Signing: verify the signature validates with the public cert.
- Submission: against **sandbox** (`P.3`) — `submitted → cleared`, QR returned, rejection handled.
- Simulation: 90-day synthetic retail tenant issues invoices, 100% clear, chain verifies (`P.1`).

---

## 5. Launch impact

| Market | e-invoicing needed at launch? | Plan |
|---|---|---|
| **Jordan** (Tier-1 beachhead) | **Not a hard blocker.** JoFotara onboarding is still rolling out per taxpayer; small businesses can operate on internal invoices and add JoFotara when ISTD requires them. | Ship `jo_jofotara` in the Tier-2 window; onboard clients as they're mandated. |
| **KSA** | **Yes — mandatory.** No compliant clearance = can't legally issue tax invoices. | KSA sales wait for `sa_zatca` GA (this spec), **or** a client uses a ZATCA-certified third-party in the interim (bridge only). |
| UAE | Monitor federal rollout. | `ae_peppol` mode, Phase 3. |

**So: the JO soft launch is not gated on this. The KSA launch is.** Build order:
`jo_jofotara` and `sa_zatca` in parallel (shared UBL builder + engine), JO first to GA
because its conformance bar is lower and it's the beachhead.

---

## 6. Immediate steps

1. M1 migration: add the `einvoice_*` fields + `EInvoiceSequence` (additive, nullable).
2. Promote `jofawtra` + `zakata` clients → `platform/einvoicing/clients/`; keep the aliases.
3. Build `platform/einvoicing/ubl.py` — `jo_jofotara` profile first, golden-file tested.
4. Build `engine.py` — submit via `JoFotaraClient` against sandbox, persist result.
5. Wire `EInvoiceEngine.clear()` into the Invoice post-flow (replace the gateway `httpx.post`).
6. Retire `cycom/compliance-gateway/` (or keep it as a thin proxy to the engine if a non-Django
   consumer needs it — decide at step 5).
7. Repeat 3–5 for `sa_zatca` (CSID onboarding is the long pole — start the ZATCA portal
   registration on day 1).
