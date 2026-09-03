# NPHIES Integration — Sandbox Onboarding

The Saudi **National Platform for Health Information Exchange Services**
(NPHIES) is CCHI's FHIR R4 clearinghouse for eligibility checks,
pre-authorisations, claims, and remittance advice between healthcare
providers and payers.

This module (`products.cymed.integrations.nphies`) implements a
sandbox-capable client:

- OAuth2 `client_credentials` at `POST /oauth2/token`
- Mutual TLS on every non-token endpoint
- FHIR bundles of `type=collection` carrying a `MessageHeader` plus the
  relevant domain resource + `Organization` / `Patient` / `Coverage`
- KSA profile URIs under `http://nphies.sa/fhir/ksa/nphies-fs`
- Caller-supplied `idempotency_key` becomes `MessageHeader.identifier.value`
- Retries only on connection-level errors (`httpx.ConnectError`,
  `ConnectTimeout`, `ReadTimeout`, `NetworkError`,
  `RemoteProtocolError`) — 4xx/5xx propagates to the caller.

---

## 1. Prerequisites

You need each of the following before the sandbox will accept traffic:

| Item                              | Where it comes from                                       |
|-----------------------------------|------------------------------------------------------------|
| CCHI provider license id          | Council of Cooperative Health Insurance (CCHI) portal      |
| NPHIES tenant registration        | `nphies.support@chi.gov.sa` (payer / provider onboarding)  |
| OAuth2 client id + secret         | Emailed by NPHIES support after tenant creation            |
| Client mTLS certificate + private key | You generate CSR → NPHIES issues signed cert            |
| Sandbox test data set name        | Provided in the onboarding pack (see §4)                   |

## 2. Payer / provider registration

1. Log into the CCHI provider portal with your national commercial
   registration (CR) and NPHIES enrollment PDF.
2. Nominate an integration owner (email address that will receive the
   sandbox invitation and the signed mTLS certificate).
3. NPHIES support responds within ~5 business days with:
   - Sandbox tenant id
   - `NPHIES_CLIENT_ID` and `NPHIES_CLIENT_SECRET`
   - Sandbox base URL (usually `https://sandbox.nphies.sa`)
   - A short URL-token to download the onboarding pack (test data,
     scenario checklists)

## 3. Generating a CSR for mTLS

NPHIES only accepts client certificates it signed itself. Generate a
2048-bit RSA CSR:

```bash
openssl req -new -newkey rsa:2048 -nodes \
    -keyout cymed-nphies-sandbox.key \
    -out cymed-nphies-sandbox.csr \
    -subj "/C=SA/O=<your legal name>/OU=CyMed/CN=<CCHI license id>"
```

Send `cymed-nphies-sandbox.csr` (never the key) to
`nphies.support@chi.gov.sa`. They return a PEM-formatted signed cert
within 24h. Concatenate the leaf and the NPHIES intermediates:

```bash
cat cymed-nphies-sandbox.crt nphies-intermediates.pem > cymed-nphies-sandbox.pem
```

Then point the env vars at the PEM cert + private key.

## 4. Sandbox test data set names

The onboarding pack ships with these named datasets you can quote in
sandbox transactions (each triggers a scripted response from the mock
payer):

| Dataset name          | Purpose                                          |
|-----------------------|--------------------------------------------------|
| `HAPPY_PATH_SAUDI`    | Fully covered Saudi national, no pre-auth needed |
| `HAPPY_PATH_IQAMA`    | Fully covered resident (Iqama id)                |
| `PREAUTH_REQUIRED`    | Coverage active, but service needs pre-auth      |
| `COVERAGE_EXPIRED`    | Policy expired 30d ago                           |
| `PARTIAL_COINSURANCE` | Coverage with 20% patient responsibility         |
| `CLAIM_REJECT_INVALID_CODE` | Triggers a scripted 400 rejection           |

Populate `member_no` and `policy_number` fields from the corresponding
CSV in the onboarding pack (`onboarding/testdata/*.csv`).

## 5. Environment variables

| Variable                   | Sandbox default                     | Required |
|----------------------------|-------------------------------------|----------|
| `NPHIES_BASE_URL`          | `https://sandbox.nphies.sa`         | no       |
| `NPHIES_AUTH_URL`          | `{NPHIES_BASE_URL}/oauth2/token`    | no       |
| `NPHIES_CLIENT_ID`         | —                                   | yes      |
| `NPHIES_CLIENT_SECRET`     | —                                   | yes      |
| `NPHIES_SCOPES`            | `nphies`                            | no       |
| `NPHIES_MTLS_CERT_PATH`    | —                                   | yes      |
| `NPHIES_MTLS_KEY_PATH`     | —                                   | yes      |
| `NPHIES_LICENSEE_ID`       | —                                   | yes      |

For production, override `NPHIES_BASE_URL` with the current NPHIES
production URL from the payer contract (they change; do not hard-code).

## 6. Endpoints exercised

| Operation                        | HTTP + Path                                     |
|----------------------------------|-------------------------------------------------|
| OAuth2 token exchange            | `POST /oauth2/token`                            |
| Coverage eligibility             | `POST /CoverageEligibilityRequest/$submit`      |
| Pre-authorisation submit         | `POST /Claim/$submit` (Claim.use=preauthorization) |
| Claim submit                     | `POST /Claim/$submit` (Claim.use=claim)         |
| Task status lookup               | `GET /Task?identifier={ref}`                    |

FHIR profiles used:

- `http://nphies.sa/fhir/ksa/nphies-fs/StructureDefinition/eligibility-request`
- `http://nphies.sa/fhir/ksa/nphies-fs/StructureDefinition/eligibility-request-bundle`
- `http://nphies.sa/fhir/ksa/nphies-fs/StructureDefinition/priorauth`
- `http://nphies.sa/fhir/ksa/nphies-fs/StructureDefinition/priorauth-bundle`
- `http://nphies.sa/fhir/ksa/nphies-fs/StructureDefinition/institutional-claim`
- `http://nphies.sa/fhir/ksa/nphies-fs/StructureDefinition/claim-bundle`
- `http://nphies.sa/fhir/ksa/nphies-fs/StructureDefinition/message-header`
- `http://nphies.sa/fhir/ksa/nphies-fs/StructureDefinition/provider-organization`
- `http://nphies.sa/fhir/ksa/nphies-fs/StructureDefinition/patient`
- `http://nphies.sa/fhir/ksa/nphies-fs/StructureDefinition/coverage`

## 7. Idempotency

Every entry point accepts an optional `idempotency_key`:

```python
client.coverage_eligibility_request(
    insurer="...", policy_number="...", member_no="...",
    service_code="99213", provider_tenant_id="...",
    idempotency_key="cymed-eligibility-<uuid>",
)
```

The key becomes `Bundle.entry[MessageHeader].identifier.value` — NPHIES
uses it to de-duplicate submissions, so a retry after a timeout is safe.

## 8. Structured logging

All log records are emitted under logger name
`cymed.integrations.nphies`. Event names include
`nphies.token.request`, `nphies.token.cached`, `nphies.eligibility.submit`,
`nphies.eligibility.failed`, `nphies.preauth.submit`, `nphies.preauth.ok`,
`nphies.preauth.failed`, `nphies.claim.submit`, `nphies.claim.ok`,
`nphies.claim.failed`, `nphies.http.request`, `nphies.http.retrying`,
`nphies.http.retry_exhausted`. Configure them in `LOGGING` in
`core/settings.py` and forward to your log aggregator.

## 9. Dependencies

- `httpx>=0.27,<1.0` (already in `requirements.txt`)

## 10. Escalation contact

- **NPHIES sandbox support:** `nphies.support@chi.gov.sa`
- **NPHIES service desk (24/7):** `+966 11 234 5000` (open a ticket
  with your CCHI license id and the affected `correlation_id`)
- **CyMed integration lead:** `integrations@cymed.local` — this team
  owns the escalation to NPHIES and will attach recent
  `NphiesInteraction` rows.

When escalating, include:

1. The `correlation_id` (visible in the `NphiesInteraction` row and in
   every log line).
2. The `MessageHeader.identifier.value` (== `idempotency_key`) so
   NPHIES can look up the submission in their audit trail.
3. Timestamp (UTC) and the HTTP status code we received.
4. The sandbox dataset name being exercised, if any.
