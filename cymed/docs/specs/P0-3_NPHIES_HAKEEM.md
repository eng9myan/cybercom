# P0-3 · NPHIES (KSA) + Hakeem (Jordan) Bridges — Technical Spec

**Owner:** CyMed Integrations · **Status:** SPEC + CODE
**Depends on:** P0-2 InsurancePolicy model, `platform.terminology`
**Blocks:** RCM Engine (P0-6) uses NPHIES claim submission

---

## 1. NPHIES (Saudi Arabia)

### What
Saudi Council of Health Insurance (CHI) mandatory platform. FHIR R4 with Saudi profiles.
Covers eligibility, pre-auth, claims, remittance, prescriptions.

Env vars:
- `NPHIES_BASE_URL` — sandbox `https://sandbox.nphies.sa/fhir/R4`, prod issued per licensee
- `NPHIES_CLIENT_ID`, `NPHIES_CLIENT_SECRET` — issued after CHI onboarding
- `NPHIES_MTLS_CERT_PATH`, `NPHIES_MTLS_KEY_PATH` — required for prod
- `NPHIES_LICENSEE_ID` — provider/payer identifier

### Endpoints implemented
| Method | Purpose | FHIR resource |
|---|---|---|
| `authenticate()` | OAuth2 client_credentials | Bearer token cached 55 min |
| `coverage_eligibility_request(...)` | verify insurance | `CoverageEligibilityRequest` |
| `preauth_submit(...)` | pre-authorization | `Claim (use=preauthorization)` |
| `preauth_status(reference)` | poll pre-auth | `Task` |
| `claim_submit(bill)` | submit final claim | `Claim (use=claim)` |
| `remittance_advice(claim_id)` | payer response | `ClaimResponse` |

### Django app
`products/cymed/integrations/nphies/`

### Files
- `client.py` — HTTP + FHIR bundle builders + response parsers
- `models.py` — audit trail (`NphiesInteraction`)
- `serializers.py`, `views.py`, `urls.py` — REST API for admin visibility
- `apps.py`, `__init__.py`, `migrations/`

---

## 2. Hakeem (Jordan)

### What
Jordan Ministry of Health national EHR (VistA/CPRS backbone). Private hospitals need
bidirectional data flow to public sector Hakeem instance.

Architecture: no public FHIR endpoint. Bridge uses:
- Hakeem's MUMPS-based RPC broker (VistaRPC) — read patient + orders
- SFTP / HL7 v2 message exchange — write results back
- Optional: emerging Hakeem FHIR proxy (2026 roadmap) — feature-flag

Env vars:
- `HAKEEM_RPC_HOST`, `HAKEEM_RPC_PORT`, `HAKEEM_RPC_ACCESS_CODE`, `HAKEEM_RPC_VERIFY_CODE`
- `HAKEEM_SFTP_HOST`, `HAKEEM_SFTP_USER`, `HAKEEM_SFTP_KEY_PATH`
- `HAKEEM_FHIR_URL` (optional 2026)
- `HAKEEM_FACILITY_CODE` — issued by EHS per hospital

### Operations
| Op | Direction | Transport | Frequency |
|---|---|---|---|
| Fetch patient by national ID | pull | VistaRPC (`ORWPT ID INFO`) | on demand |
| Fetch patient meds | pull | VistaRPC (`ORWPS ACTIVE`) | on demand |
| Fetch lab results | pull | VistaRPC (`ORWLRR INTERIM`) | on demand |
| Push lab result | push | HL7 v2 ORU^R01 via SFTP | on event |
| Push encounter summary | push | HL7 v2 MDM^T02 | on discharge |

### Django app
`products/cymed/integrations/hakeem/`

### Files
- `client.py` — VistaRPC + SFTP + HL7 v2 + optional FHIR fallback
- `models.py` — `HakeemMessage` audit
- `hl7_builder.py` — construct ORU^R01, MDM^T02 messages
- `mumps_rpc.py` — thin wrapper over VistaRPC broker

---

## 3. Rollout
- Sandbox first: NPHIES sandbox + Hakeem test facility
- Cert-signing for prod: 4-6 weeks per bridge
- Fail-open on eligibility (allow visit, flag review) if bridge down
