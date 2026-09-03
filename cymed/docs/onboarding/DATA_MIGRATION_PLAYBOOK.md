# Data Migration Playbook

| Field | Value |
|---|---|
| Version | 0.1 (Draft) |
| Date | 2026-08-19 |
| Owner | `<Head of Data Engineering — TBD>` |
| Review cadence | Semi-annually |

---

## 0. Purpose

Standard, repeatable process for migrating clinical, administrative, and imaging data from a Customer's legacy system(s) into a CyMed tenant. Applies to Clinic, Hospital, Lab, Imaging, and Pharmacy editions.

## 1. Six-step Migration Workflow

### Step 1 — Legacy Inventory

Deliverable: **Legacy Source Register** (`docs/onboarding/artifacts/legacy_register_<tenant>.md`).

For each source system, record:
- Name, vendor, version, criticality.
- Access method (direct DB, API, file export, screen scrape as last resort).
- Data volumes (rows, GB, DICOM studies count and TB).
- Character sets, timezone, date formats, locale.
- Known data-quality issues (duplicates, missing PKs, orphaned refs).
- Business owner + technical owner.
- Legal / regulatory retention rules affecting the data.

### Step 2 — Map to CyMed Schema

Deliverable: **Mapping Book** — one worksheet per entity.

Rules:
1. Prefer FHIR R4 resources for clinical data (`Patient`, `Encounter`, `Condition`, `Observation`, `MedicationRequest`, `MedicationDispense`, `DiagnosticReport`, `ImagingStudy`, `Coverage`, `Claim`).
2. Prefer DICOM for imaging; store studies via SCP or study-level import; index in RIS by `StudyInstanceUID`.
3. Normalise identifiers: national ID / MRN / MPI must map to `Patient.identifier` with system URIs; keep original ID as a secondary identifier for reconciliation.
4. Terminologies: map codes to SNOMED CT / ICD-10 / LOINC / RxNorm / national code sets (Saudi drug code, etc.) via lookup tables committed alongside the ETL scripts.
5. Preserve legacy PKs in a shadow column (`source_pk`) for audit and re-run.

### Step 3 — Build ETL

Deliverable: ETL scripts committed under `D:/cybercom/cymed/tools/migration/`.

Repo layout:

```
D:/cybercom/cymed/tools/migration/
  README.md
  common/                   # shared utils (id-hashing, tz normalisation, code lookups)
  sources/
    <legacy-system-name>/
      01_extract/           # extract from source to landing (CSV / Parquet)
      02_transform/         # normalise + map to CyMed schema
      03_load/              # loaders into a staging tenant
      04_verify/            # reconciliation queries + reports
      config.yaml           # source-specific config (conn strings from vault, not committed)
      README.md             # per-source migration notes
  lookups/                  # code cross-walks (SNOMED, ICD10, LOINC, RxNorm, national codes)
  fixtures/                 # tiny anonymised sample data for unit tests
  tests/                    # unit + integration tests
```

Coding rules:
- Idempotent loads (safe re-run); use `source_pk` for upsert.
- Structured logs (JSON) with per-row correlation ids.
- Never write PHI to logs; only counts and hashes.
- All secrets from vault or env; nothing committed.
- Every script has a `--dry-run` mode that reads and validates without writing.
- Unit tests use anonymised fixtures in `tests/`.

### Step 4 — Dry-run against Staging Tenant

- Full-volume load into a dedicated staging tenant configured identically to production.
- Two dry-runs minimum; a third if reconciliation shows non-trivial discrepancies.
- Timeboxed. Cut-over runbook estimates production cut-over from measured dry-run durations.
- After each dry-run, staging is reset to a snapshot to allow re-runs from a clean baseline.

### Step 5 — Reconciliation Report

Deliverable: **Reconciliation Report** (`docs/onboarding/artifacts/recon_<tenant>_<date>.md`).

At minimum, report:

| Layer | Checks |
|---|---|
| Row counts | Source count vs. staged count per entity. Explain each variance. |
| Financial totals | Sum(invoice.amount), sum(payment.amount), sum(claim.charge) by period, currency, and payer. |
| Clinical anchor lists | Active patient count; open encounter count; active medication count; active problem count. |
| Sample records | 30 random patients: side-by-side legacy vs. CyMed view; clinician sign-off required. |
| Cross-references | Orphaned foreign keys; unmapped codes; unmapped payers. |
| Referential integrity | Every `Encounter.subject` resolves; every `MedicationRequest.encounter` resolves; etc. |
| Duplicates | Duplicate patient candidates (MPI similarity ≥ threshold). Manual review required. |
| Imaging | For each DICOM `StudyInstanceUID`: images-in-source vs. images-in-PACS; hash on a sample. |

Reconciliation Report must be signed by CustPM + CyTL + CustClin before Go / No-go review.

### Step 6 — Cut-over

See template below. All fields must be filled in before cut-over.

## 2. Cut-over Window — Template

| Field | Value |
|---|---|
| Tenant | `<tenant-id>` |
| Cut-over window | `<YYYY-MM-DD hh:mm–hh:mm tz>` |
| Freeze window (legacy writes stop) | `<start – end>` |
| Fallback window | `<until when>` |
| Command centre | `<location / bridge>` |
| War room roster | See §2.3 |
| Rollback trigger conditions | See §2.5 |

### 2.1 Preconditions (must all be YES)

- [ ] Dry-run 2 reconciliation signed.
- [ ] UAT sign-off in place.
- [ ] Security review closed.
- [ ] Backups verified for both legacy and CyMed staging.
- [ ] Runbook rehearsed end-to-end (no live cut-over).
- [ ] Support channels open (SEV1 hotline, WhatsApp/Teams war room, status page).
- [ ] Clinical fall-back procedures printed at every ward station.
- [ ] Downtime forms and paper kits distributed.
- [ ] Executive sponsor on standby (reachable within 5 minutes).

### 2.2 Cut-over Steps (illustrative)

| # | Time | Owner | Action |
|---:|---|---|---|
| 1 | T-24 h | CyPM | Final go/no-go call |
| 2 | T-4 h | CustIT | Legacy system placed in read-only |
| 3 | T-3 h | CyTL | Delta ETL run since last dry-run |
| 4 | T-2 h | CyTL | Reconciliation delta report |
| 5 | T-1 h | CustClin | Clinical spot checks on random patients |
| 6 | T-30 m | CyTL | Integration endpoints switched over |
| 7 | T-0 | CustExec | Announce cut-over live |
| 8 | T+15 m | CyClin | End-to-end smoke test in production |
| 9 | T+1 h | CyPM | First status update |
| 10 | T+4 h | CyPM | Cut-over stability call |
| 11 | T+24 h | CyPM | Cut-over report v1 |

### 2.3 War-room roster (template)

| Role | Name | Contact |
|---|---|---|
| CustExec | `<name>` | `<phone>` |
| CustPM | `<name>` | `<phone>` |
| CustClin lead | `<name>` | `<phone>` |
| CustIT lead | `<name>` | `<phone>` |
| CustRCM lead | `<name>` | `<phone>` |
| CyPM | `<name>` | `<phone>` |
| CyTL | `<name>` | `<phone>` |
| CyClin | `<name>` | `<phone>` |
| CySec | `<name>` | `<phone>` |
| CyMed on-call SEV1 | `<pager>` | `<phone>` |

### 2.4 Communications plan

- Public: status page + tenant banner.
- Internal (Customer): all-staff email at T-24 h, T-1 h, T-0, T+4 h.
- Clinical: unit-level briefings the day before; laminated one-pager.
- External integrations: partner notifications 5 business days in advance; test call at T-2 h.

### 2.5 Rollback triggers and procedure

Rollback the cut-over if any of the following occurs in the first 4 hours after T-0:
- **Any** SEV1 patient-safety issue reproducible in production.
- Reconciliation delta > 0.5% on financial totals or > 0.1% on patient count.
- Integration failure blocking a critical workflow with no workaround.
- Loss of DICOM ingress for > 30 minutes with imaging queue growing.

Rollback procedure:
1. CustExec + CyPM jointly authorise rollback.
2. CyTL disables incoming writes to CyMed for the tenant.
3. Legacy system returned to read/write; export from CyMed of any writes since T-0 (using audit log).
4. Post-rollback review within 24 h; new cut-over date proposed within 5 business days.

## 3. Post-cut-over

- CyMed keeps legacy landing / staging tenants retained for **60 days** for forensic reconciliation.
- Reconciliation delta reports at T+7 d, T+30 d, T+60 d.
- Legacy source retention thereafter per Customer's records-retention policy.
