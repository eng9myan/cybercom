# P0-6 · RCM Engine — Spec + Code

**Owner:** CyMed Revenue Cycle · **Status:** SPEC + CODE
**Depends on:** P0-2 payments, P0-3 NPHIES, P0-4 FHIR, P0-5 AI CDS
**Blocks:** none

## Goals
- Automate hospital revenue cycle: eligibility → coding → claim → denial → appeal.
- Reduce denial rate from ~12% industry avg to <5%.
- Prior-auth automation per CMS 7-day/72-hr rules.

## Modules
| Module | Purpose |
|---|---|
| `engines/coding.py` | Auto ICD-10/CPT from clinical notes (uses ai_cds ICDNLPEngine) |
| `engines/scrubber.py` | Pre-submit claim validation — missing fields, invalid codes, payer rules |
| `engines/denial_predictor.py` | ML-scored denial risk before submit |
| `engines/payer_rules.py` | Per-payer rule sets (Tawuniya, Bupa, MedGulf, NSSF) |
| `engines/preauth.py` | Prior-auth workflow orchestrator |
| `engines/appeals.py` | Denial → appeal letter generation |

## Data model
- `Claim837` — 837P/837I claim submission record
- `ClaimResponse` — payer decision
- `DenialCode` — CARC / RARC lookup
- `AppealCase` — appeal workflow
- `EligibilityCache` — 24-h TTL cache on eligibility

## Endpoints (base `/api/v1/rcm/`)
```
POST /claims/build              { encounter_id } → Claim837 draft
POST /claims/{id}/scrub          → validation report
POST /claims/{id}/predict-denial → { risk, drivers }
POST /claims/{id}/submit         → routes to NPHIES / JoFotara
GET  /claims/{id}                → status + ClaimResponse
POST /claims/{id}/appeal         → AppealCase
GET  /denials/                   → all open denials
GET  /denials/{id}                → detail
POST /denials/{id}/resubmit       → new Claim837
GET  /preauth/                    → PreAuthorization list (from payments app)
POST /preauth/                    → create + submit
GET  /kpis/                       → denial rate, DSO, first-pass rate, AR aging
```
