# JoFotara (Jordan) e-invoicing integration

> Package: `products.cymed.integrations.jofawtra`
> Django app label: `cymed_int_jofawtra`
> Vendor: Jordan Income & Sales Tax Department — JoFotara / نظام الفوترة
> Standard: UBL 2.1 with customization ID **`PINT-JO`**, XAdES-signed in prod

## Overview

CyMed submits every billable clinical/pharmacy/imaging invoice to JoFotara for
clearance and QR issuance. Traffic is routed through
[`JoFotaraClient`](./client.py) which uses `httpx` (never `requests`) and
supports both HTTP Basic and Bearer authentication.

Legacy call sites keep working via the `JoFawTraClient` / `JoFawtraClient`
aliases exported from the same module.

## Public API

```python
from products.cymed.integrations.jofawtra.client import JoFotaraClient

client = JoFotaraClient()  # env-driven; inject overrides in tests
resp = client.submit_invoice(ubl_xml=signed_xml, invoice_uuid="4c8e...")
# {'status': 'submitted', 'reference': 'JO-2026-000123', 'raw': {...}}

status = client.check_status(resp["reference"])
# {'status': 'cleared', 'reference': '...', 'raw': {...}}
```

Constructor kwargs (all optional; fall back to env vars):

| kwarg | env var | purpose |
| --- | --- | --- |
| `base_url` | `JOFOTARA_BASE_URL` | API root; sandbox default `https://sandbox.jofotara.gov.jo` |
| `client_id` | `JOFOTARA_CLIENT_ID` | issued to your taxpayer profile |
| `client_secret` | `JOFOTARA_CLIENT_SECRET` | paired secret |
| `tax_id` | `JOFOTARA_TAX_ID` | issuer TIN (goes into `Client-Id` header) |
| `activity_code` | `JOFOTARA_ACTIVITY_CODE` | ISIC-4 code registered with ISTD |
| `auth_kind` | `JOFOTARA_AUTH_KIND` | `basic` (default) or `bearer` |
| `private_key_path` | `JOFOTARA_PRIVATE_KEY_PATH` | PEM key used for XAdES signing |
| `client` | — | pre-built `httpx.Client` for tests / connection reuse |

## Endpoints

| Purpose | Method | Path |
| --- | --- | --- |
| Submit signed UBL | `POST` | `/invoicing/submit` |
| Poll submission status | `GET` | `/invoicing/status/{reference}` |
| OAuth2 token (bearer mode only) | `POST` | `/oauth/token` |

## Signing (XAdES)

Production submissions must be XAdES-enveloped-signed with the taxpayer's
private key. `JoFotaraClient._sign_xml` is the hook — wire your XAdES signer
here (e.g. `signxml` or `xmlsec` bindings). If `JOFOTARA_PRIVATE_KEY_PATH`
is not configured, the client **logs a warning and submits the UNSIGNED
payload**. That is safe for sandbox smoke tests only; do not run unsigned
against production.

## Environment variables

```bash
# sandbox defaults are safe; override for staging/prod
export JOFOTARA_BASE_URL=https://sandbox.jofotara.gov.jo
export JOFOTARA_CLIENT_ID=...            # required
export JOFOTARA_CLIENT_SECRET=...        # required
export JOFOTARA_TAX_ID=200123456         # 9-digit issuer TIN
export JOFOTARA_ACTIVITY_CODE=8610       # ISIC-4
export JOFOTARA_AUTH_KIND=basic          # or "bearer"
export JOFOTARA_PRIVATE_KEY_PATH=/etc/cymed/jofotara.pem
```

Never commit real client secrets or private-key material to the repo.

## Sandbox onboarding

1. **Register the taxpayer** on the ISTD JoFotara portal (`istd.gov.jo` →
   e-Invoicing) with the medical facility's TIN and ISIC-4 activity code
   (`8610` for hospital, `8620` for medical/dental, `4772` for pharmacies).
2. **Request sandbox credentials** by opening a ticket with ISTD support
   (`jofotara-support@istd.gov.jo`), attaching:
   * signed integrator agreement,
   * the fixed IP range CyMed will call from (whitelisting is required),
   * a technical contact e-mail for the OTP flow.
3. **Receive** the sandbox `CLIENT_ID` / `CLIENT_SECRET` bundle, the sandbox
   base URL, and a test XAdES signing certificate (PEM).
4. **Set the environment variables** listed above in your deployment secret
   store (Vault / AWS Secrets Manager / K8s Secret — not `.env`).
5. **Smoke-test** with a scripted `submit_invoice` → `check_status` cycle
   against sandbox. Confirm `raw.status` transitions from `submitted` to
   `cleared` and that a QR string comes back.
6. **Promote to production** only after ISTD approves your conformance
   report. Flip `JOFOTARA_BASE_URL` to the production URL supplied by ISTD
   and rotate the client secret + signing cert.

## Dependencies

`httpx` is already declared in
[`requirements.txt`](../../../../requirements.txt); no new package is added
for this integration.
