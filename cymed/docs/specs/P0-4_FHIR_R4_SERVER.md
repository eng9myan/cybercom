# P0-4 · FHIR R4 REST Server — Spec + Code

**Owner:** CyMed Platform · **Status:** SPEC + CODE
**Depends on:** core.patients, clinical.observations, clinical.conditions, prescriptions, encounters
**Blocks:** RCM (needs FHIR Claim), Patient App PWA extended data

---

## Goals
- Expose CyMed's clinical data as **FHIR R4 REST server** at `/fhir/R4/`.
- Full CRUD for the 12 core resources needed by NPHIES + JoFotara + third-party integrations.
- Bundle transaction, `_include`, `_revinclude`, `_search` params.
- OAuth2 SMART-on-FHIR launch flow (auto-negotiated with CyIdentity).

## Resources implemented
| Resource | CyMed source model | Endpoints |
|---|---|---|
| Patient | `core.patients.Patient` | GET/POST/PUT · search: identifier, family, given, birthdate, gender, telecom |
| Encounter | `core.encounters.Encounter` | GET/POST/PUT · search: patient, status, type, date |
| Observation | `clinical.observations.Observation` | GET/POST · search: patient, code, category, date, value-quantity |
| Condition | `clinical.conditions.Condition` | GET/POST · search: patient, clinical-status, code |
| AllergyIntolerance | `clinical.allergies.Allergy` | GET/POST · search: patient, criticality |
| MedicationRequest | `pharmacy.prescriptions.Prescription` | GET/POST · search: patient, status, authoredon |
| DiagnosticReport | `laboratory.results.Report` | GET · search: patient, category, code, date |
| ImagingStudy | `imaging.studies.Study` | GET · search: patient, modality, started |
| Coverage | `payments.InsurancePolicy` | GET/POST · search: patient, payor |
| Claim | `payments.UnifiedBill` | GET/POST · search: patient, status, use |
| ExplanationOfBenefit | derived from Claim + ClaimResponse | GET |
| DocumentReference | `platform.documents` | GET/POST |

## Endpoints
```
GET   /fhir/R4/metadata               → CapabilityStatement
POST  /fhir/R4/                        → Bundle transaction / batch
GET   /fhir/R4/{Resource}             → search
POST  /fhir/R4/{Resource}             → create
GET   /fhir/R4/{Resource}/{id}        → read
PUT   /fhir/R4/{Resource}/{id}        → update
DELETE /fhir/R4/{Resource}/{id}       → delete (soft)
GET   /fhir/R4/{Resource}/{id}/_history → history
GET   /fhir/R4/{Resource}/$validate    → validation
```

Django app: `products/cymed/fhir_r4/`

## Files
- `capability.py` — CapabilityStatement generator (rest of app registers into it)
- `mappers/patient.py`, `.../encounter.py`, etc — bidirectional CyMed↔FHIR mappers
- `views.py` — one generic `FHIRResourceView` + resource registry
- `bundle.py` — bundle transaction executor
- `search.py` — FHIR search-param parser + Django Q builder
- `urls.py`
