# CyMed — Full System Audit

**Engagement:** Multi-disciplinary functional / workflow / design / localization audit
**Method:** Live stack (`core.settings_local`, SQLite, `KEYCLOAK_ENABLED=False`), seeded hospital sim. API-driven clinical/RCM/pharmacy/lab/imaging cycle testing + code review + test suite (`run_tests.py` / pytest). CyMed ships **no SPA frontend** in this repo — UI is 4 Django-templated portal shells — so design/bilingual-UI personas are scoped to those + the RN patient app.
**Audit run:** 2026-09-08 (in progress)
**Repo:** `D:\cybercom\cymed` (canonical; `D:\CyMed-Claude`, `D:\CyMed-Final-extracted` are parallel/older copies — ignored)

---

## STATUS: v1 COMPLETE + P0 FIXES APPLIED & VERIFIED (2026-09-08)

**P0 remediation done** (live-verified against the seeded hospital sim; 9/9 P0 checks pass):

| P0 | Fix | Verified |
|---|---|---|
| **M-1** fresh `migrate` fails | Generated the missing `provider_portal/migrations/0001_initial.py`; a truly fresh `manage.py migrate` now **completes in one pass** (exit 0, all ~285 migrations) | ✅ empty-DB migrate → OK end-to-end |
| **M-5** PHI crypto breaks on UUID form | `platform/security/crypto.py` `_canonical_tenant_id()` normalises every tenant-id representation to the canonical hyphenated UUID before the HKDF salt; `AuditService._chain_key` normalised too; `EncryptedText.from_db_value` now catches `FieldDecryptionError` → returns a `⚠ unavailable` sentinel instead of 500 | ✅ hex-form tenant `GET /patients/` → **200** (was 500), all encrypted fields decrypt |
| **M-6** name + MRN plaintext | `Patient.first_name/last_name/mrn` → `EncryptedText(blind_index=True)`; MRN uniqueness moved to `mrn_bidx` UniqueConstraint; ordering → `-created_at`; data migration `0008` re-encrypts existing rows + populates blind indexes | ✅ DB shows `b'cc1…'` ciphertext + `*_bidx`; API decrypts on read |
| **M-7** no RBAC / no prod auth | New `platform/api/authentication.py::ClaimsAuthentication` (bridges the CyIdentity token → `request.user`); `platform/api/permissions.py::IsAuthenticatedClinicalStaff` (deny-by-default staff-role gate) + `IsAuthenticatedPatient` + `require_roles()`; wired as CyMed prod `DEFAULT_AUTHENTICATION_CLASSES` / `DEFAULT_PERMISSION_CLASSES`; codemod aliased the 24 viewsets that pinned stock `IsAuthenticated` | ✅ no-auth → 401, patient-token → **403**, staff token → 200 |
| **M-11** no PHI audit trail | New `platform/audit/middleware.py::PHIAccessAuditMiddleware` records a hash-chained `AuditEvent` (via the existing, previously-uncalled `AuditService`) for every clinical/PHI API request — actor, tenant, resource, purpose-of-use, outcome; wired into CyMed `MIDDLEWARE` | ✅ events written + hash-chained (one chain per tenant); `verify_chain` returns a result |
| _bonus_ **M-8** no API throttle | CyMed prod `DEFAULT_THROTTLE_CLASSES` = User+Anon rate throttles (2000/h, 60/h) | ✅ |

Files changed: `platform/security/crypto.py`, `platform/common/fields.py`, `platform/audit/{middleware.py (new), services.py}`, `platform/api/{authentication.py (new), permissions.py}`, `cymed/core/settings.py`, `cymed/products/cymed/core/patients/{models,serializers,services}.py` (+migrations `0007`, `0008`), `cymed/products/cymed/**/views.py` (24 files — `IsAuthenticated` alias), `cymed/products/cymed/core/tests/test_clinical_core.py` (updated for the M-6 encryption change).

**M-6 collateral, fixed:** `PatientService.detect_duplicates` (and the `/patients/search` MPI action) fuzzy-matched names via `first_name__icontains` — impossible on an encrypted column. Rewritten to narrow on `dob` (plaintext, indexed) then fuzzy-compare decrypted names in Python (`SequenceMatcher`, first-3-char prefix). **Remaining limitation:** a pure name-only search with no DOB / ID is no longer possible — a phonetic blind-index (Soundex/Metaphone tokens) is the P1 follow-up.

**M-2 (no clinician UI)** is a product decision (build vs partner), not a code fix — unchanged. Remaining P1/P2 findings (M-3 test collection, M-12–M-18 interaction engine / FHIR / consent) unchanged.

**Test impact:** `TestPatientsModule` (3 tests) green after the M-6 collateral fixes. Full `products/cymed` suite re-running for a clean count (was 103 passing pre-fix; the 2 failures were both M-6 test-collateral, now fixed).

Notes: `verify_chain` still reports the seq-1 event as invalid — a **hash-determinism bug in the verifier** (`AuditEvent.compute_hash` stringifies `timestamp` with microseconds; the reload rounds) — pre-existing, now surfaced because the chain is finally populated. Follow-up: make `compute_hash` use an ISO-8601 canonical timestamp.

---

## STATUS: v1 (audit) COMPLETE — API + code; live UI pass still needs a browser

| Persona | Status |
|---|---|
| Stack / build / deploy | done — **M-1 Critical**, M-3 High |
| IT Administration & Security | done — **M-5 Critical**, M-6/M-7 High, M-8/M-9/M-10, M-19 |
| Patient Administration (ADT) | done — 293 patients / 72 admissions live; findings folded into M-5/M-7/M-11 |
| Clinical (encounters, orders, CDS scores) | done — CDS NEWS2/sepsis compute OK; M-16 (override attribution) |
| Pharmacy (interactions, dispensing) | done — **M-12–M-15** (interaction engine); dispensing gated 403 |
| Laboratory / Imaging / Radiology | done (light) — endpoints 403-gated (M-19); no seed data for full flow (M-20) |
| Revenue Cycle (RCM, NPHIES/Hakeem) | light — `rcm/kpis` shape OK; no claims seeded (M-20) |
| Scheduling & Reception | light — 465 appointments live |
| Compliance (FHIR R4, consent, audit chain, clinical safety) | done — **M-11 Critical**, M-17, M-18 |
| UX/UI (4 portal templates + RN patient app) | source-reviewed only — M-2; **live pass still needs Chrome extension** |
| Bilingual Localization (django.po, 96 strings) | done — M-4 |
| Prospective Buyer verdict | **done** (below) |

_Scan window for the audit: live stack `core.settings_local` (SQLite, JWKS patched), seeded `seed_hospital_sim --scale 0.3`. API-driven + code review. No browser (extension not connected) so the 4 portal templates + RN app got source review only._

---

## SURFACE MAP

### Product app groups (`products/cymed/`, ~140 Django apps)
ai_cds, clinic (appointments, billing_bridge, clinical_forms, consultations, ecommerce, insurance_bridge, marketing, queues, referral_loop, referrals, self_checkin, specialties, telemedicine, triage), clinical, commercial (branding, customer_management, deployment_profiles, editions, feature_flags, licensing, partner_management, product_catalog, subscriptions, usage_metering), consents, core, documents, ecosystem (analytics, credentialing, provider_directory, referral_routing, rewards, shared_capacity), encounters, facilities, fhir_r4, hospital (adt, anesthesia, bed_management, capacity_management, clinical_command_center, discharge, emergency, icu, inpatient, maternity, nursing, operating_room, transfer_center), imaging (img_* : ai_triage, dicom, image_sharing, pacs, patient_booking, patient_results, prep_instructions, reporting, scheduling, tele_marketplace, teleradiology, worklist), integrations (int_hakeem, int_nphies), laboratory (lab_* : accessioning, analytics, blood_bank, courier_tracking, dtc_catalog, histopathology, home_collection, microbiology, online_booking, orders, patient_results, pathology, quality, reference, results, specimens, worklists), mrff (ai_diagnostics, ambient_scribe, offline_kit, population_health), orders, organizations, patient_portal, patients, payments, pharmacy (pharmacy_* : analytics, automation, clinical, compounding, delivery, dispensing, ecommerce, formulary, interactions, inventory, loyalty, pos_insurance, prescriptions, procurement, reconciliation, robotics), providers, provider_portal, rcm, reception, registries, scheduling, simulations

### UI surface
`templates/`: `base.html`, `dashboard/index.html` (96 lines), `patient_portal/index.html`, `provider_portal/index.html` (140 lines, `{% trans %}`, EN/ع switch), `patient_app/index.html`. Plus `mobile/patient_app/` (React Native).

---

## FINDINGS

### Stack / build

**M-1 (Critical) — A fresh `manage.py migrate` does not complete; CyMed cannot be stood up from clean with the documented steps.**
Two distinct defects found bringing up an empty DB:
 1. **`provider_portal` had an empty `migrations/` directory** — no `__init__.py`, no `0001_initial.py`. Because the package was missing, `makemigrations --check` *silently ignored the app* (reported "no changes") and `migrate` never created `cymed_provider_portal_profiles` / `_activities` / `cymed_provider_credentialing_status`. The app's models/serializers/views/urls are all wired, so the whole provider-portal feature is dead on any fresh deploy and its endpoints 500 on first query. (Audit generated `0001_initial.py` locally to proceed — this migration must be committed.)
 2. **Migration dependency graph is incomplete** — a full `migrate` aborts mid-run with `OperationalError: no such table: platform_tenants` → `TransactionManagementError`, because some app migration references `platform.tenant` tables without declaring a `dependencies` edge on `platform_tenant`. `migrate platform_tenant` alone succeeds; the ordering only breaks in a combined run. Workaround is app-by-app migration; that is not acceptable for a product install.
Expected: `migrate` on an empty DB completes in one pass, then `seed_hospital_sim` runs clean. Fix: regenerate/commit `provider_portal` migrations; audit `dependencies=[]` across all app migrations that touch `platform_*`/cross-app models; add CI: empty-DB `migrate` + `seed_hospital_sim` must pass.
Persona: IT, Buyer.

**M-2 (High) — CyMed ships no clinician-facing application UI.**
140+ backend apps (ADT, ICU, OR, ED, nursing, pharmacy dispensing, lab worklists, PACS…) but the only UI is 4 Django-templated portal shells (dashboard, patient portal, provider portal, patient app) + a React Native patient app. There is no EMR / nurse station / OR board / dispensing screen / radiology reporting UI. Expected for an "enterprise hospital ERP": clinician workflows have screens. Actual: API-only. A hospital cannot run on this without a separate front-end build. Fix: scope and build the clinical UI, or partner; be explicit with buyers about what's delivered.
Persona: Buyer, Clinical, UX.

**M-3 (High) — The security + clinical-safety test suites do not run in a full-tree invocation.**
`pytest` (and `python run_tests.py` with tree args) aborts at collection: `tests/test_p10_security.py` and `tests/test_p10_clinical_safety.py` → `ModuleNotFoundError: No module named 'tests.test_p10_security'` → "Interrupted: 2 errors during collection" → **0 tests run**. They collect and pass only when named explicitly (43 tests). pytest aborts the whole run on collection errors, so any CI that runs the tree either excludes these two files or is silently green-on-nothing. The two most safety-relevant suites (auth/audit + drug-interaction/allergy/CDS guardrails) are exactly the ones excluded. Fix: resolve the `tests/` package import (rootdir / `pythonpath` / `consider_namespace_packages`), add `--strict` collection to CI, assert a minimum test count.
Persona: IT, Compliance, Clinical safety.

### Compliance & Clinical Safety

**M-11 (Critical) — There is no PHI-access audit trail. The audit models are never written to.**
`platform_audit` ships `AuditEvent` / `AuditLog` with `previous_hash` / `entry_hash` / `chain_sequence`, an `AuditChain` tip tracker, and `verify_chain` tooling — ADR-0028 "immutable, hash-chained, tamper-evident audit sink." But: `core/middleware/audit.py` `AuditMiddleware` only does `logger.info(json.dumps(...))` — it never touches the DB. `grep` across all of `products/cymed` + `platform` for `AuditEvent.objects.create` / `record_audit` / `emit_audit` → **zero hits**. Live: after seeding 293 patients / 680 encounters / 2508 orders and running PHI-read API calls, `platform_audit_events` = **0**, `platform_audit_chains` = **0**, `POST /api/v1/audit/events/verify_chain/` → `[]`. HIPAA §164.312(b), GDPR Art. 30, NPHIES and Hakeem all mandate logging every PHI access — CyMed logs none. Fix: wire a real audit emitter (DRF middleware / viewset mixin / model signals) that writes hash-chained `AuditEvent` rows for every read and write of clinical data, tenant-scoped, with actor + purpose-of-use; then the existing `verify_chain` becomes meaningful.
Persona: Compliance, IT/Security, Buyer. **Launch-blocking.**

**M-12 (High) — Drug-interaction engine (`ai_cds`) is a 6-pair hardcoded stub, matched by exact lowercase name, and 500s on any malformed input.**
`ai_cds/engines/interactions.py` `InteractionEngine.KNOWN_MAJOR` = 6 tuples (`warfarin/aspirin`, `warfarin/clopidogrel`, `warfarin/amiodarone`, `simvastatin/clarithromycin`, `sildenafil/nitrates`, `mao_inhibitor/ssri`). Matching is `dname in active_names` on lowercase display names — so "Coumadin", "ASA", RxNorm codes, NDCs all miss. `DrugContext.rxnorm` is a required field the engine never reads. `POST /api/v1/ai-cds/interactions/check/` with `{}`, `{"drugs":[...]}`, or a med lacking `rxnorm` → **HTTP 500** (`KeyError`/`TypeError`, no serializer). A clinical-safety endpoint must fail to 400, never 500 (a 500 = no check ran = silent safety gap). Fix: input serializer; drug-knowledge DB (First Databank / Lexicomp / RxNorm normalization); the endpoint is advisory-grade at best today.
Persona: Clinical safety, Pharmacy, Compliance.

**M-13 (High) — Allergy checking has no drug-class / cross-sensitivity logic.**
Same engine: `if dname in allergies` — exact string. Live: patient allergy `"penicillin"`, order `"amoxicillin"` (a penicillin) → `alerts: []`. Beta-lactam cross-reactivity, sulfa cross-reactivity, NSAID class — none detected. This is the highest-value allergy check and it isn't done. Fix: class-based allergy matching via the drug-knowledge DB.
Persona: Clinical safety.

**M-14 (High) — The interaction/allergy check trusts caller-supplied context instead of the medical record.**
`InteractionCheckView` builds `PatientContext` from `request.data` (`allergies`, `active_meds` passed in the body). It never loads the patient's real allergy list or active medication list from the DB. A caller (CPOE screen, pharmacy) that omits or under-populates those fields gets a clean result with no safety checking. Fix: resolve allergies + active meds server-side from the patient record; caller context is supplementary only.
Persona: Clinical safety.

**M-15 (Medium) — Two divergent drug-interaction engines; the stronger one is gated off.**
`ai_cds.InteractionEngine` (the stub above, exposed at `/api/v1/ai-cds/interactions/check/`) and `pharmacy/drug_interactions` (proper: `InteractionRule` DB model, `InteractionCheckSerializer` validation, `override_allowed`, `InteractionOverrideSerializer`, allergies/diagnoses/pregnancy inputs). The pharmacy engine is gated by `required_feature = "pharmacy.interactions"` — live it returns **403** (feature flag off / role) — so in this deployment only the weak engine is reachable. Fix: converge on one engine (the pharmacy one), enable it, retire `ai_cds`'s.
Persona: Clinical safety, Pharmacy, IT.

**M-16 (High) — CDS alert override does not capture who overrode or persist the reason reliably.**
`CDSAlertViewSet.acknowledge`: `acknowledged_by = request.user.id if request.user.is_authenticated else None`. With `DEFAULT_AUTHENTICATION_CLASSES = []`, `request.user` is always `AnonymousUser` → `acknowledged_by` is **always None**. Overriding a sepsis / interaction / fall-risk alert is unattributed. Clinical governance requires the overriding clinician's identity + reason on every override. Fix: read the actor from `request.user_session`; make `override_reason` mandatory when `overridden=True`.
Persona: Clinical safety, Compliance.

**M-17 (Medium) — Consent records accept no signature and an unvalidated `policy_rule`.**
`POST /api/v1/consents/` → 201 with `signature: null`, `policy_rule: "OPTIN"` (free string, not enum-checked), `status: "active"`. An active treatment/data-sharing consent with no signature and no captured grantor is not defensible. Also: no evidence anything **enforces** a consent on data access (ties to M-7 — clinical endpoints have no authz, so a `deny data_sharing` consent can't be honored). Fix: require signature (or explicit verbal-consent capture) for active consent; validate `policy_rule`; wire consent checks into the data-access path.
Persona: Compliance.

**M-18 (Medium) — FHIR R4 API is broken and minimal.**
`/fhir/R4/metadata` → 200 (fhirVersion 4.0.1) but advertises only 4 resources: Claim, Coverage, Observation, Patient. `/fhir/R4/Patient/{id}` and `/fhir/R4/Patient?_count=1` → **HTTP 500** — mappers use wrong Django app labels: `apps.get_model("patients","Patient")` (real label `cymed_patients`), `("observations"/"clinical","Observation")`, etc. So Patient and Observation reads crash; no Encounter / Condition / MedicationRequest / AllergyIntolerance / DiagnosticReport / ServiceRequest / Procedure. Fix: correct the app labels; add the core clinical resources; add a conformance test against the FHIR validator.
Persona: Compliance, Integrations, Buyer.

### IT Administration & Security

**M-5 (Critical) — Field-level PHI encryption key derivation is not UUID-canonicalisation-safe → whole-tenant PHI becomes undecryptable (hard 500).**
`platform/security/crypto.py` `_tenant_dek(tenant_id)` uses `str(tenant_id)` directly as the HKDF salt with no normalization. The encrypted `cymed_patients.national_id` decrypts **only** with the canonical hyphenated lowercase form `bbfe2d3c-128b-4268-8985-dc2e60ca7726`; the hex form `bbfe2d3c128b...` (how `platform_tenants.id` is stored in SQLite, and a plausible JWT-claim / `X-Tenant-ID` form) and any upper-case form → `FieldDecryptionError`. Live repro: `GET /api/v1/patients/` with a token whose `tenant_id` claim is the hex form → **HTTP 500** (`cryptography InvalidTag` → `FieldDecryptionError`, uncaught, reaches DRF). Expected: DEK derivation normalises the tenant id (parse to `uuid.UUID`, canonical str) so representation can't change the key; and a decryption failure degrades gracefully (field-unavailable), never a 500 on a list endpoint. Fix: normalise in `_tenant_dek`; catch `FieldDecryptionError` in the encrypted-field descriptor/serializer; add a test that all 4 UUID forms derive the same DEK.
Persona: IT/Security, Compliance, Clinical.

**M-6 (High) — Inconsistent PHI protection: patient name and MRN stored in plaintext.**
`cymed_patients.first_name` = `'Sami'`, `last_name` = `'Mansour'`, `mrn` = `'CUSH-905-000000-cym'` — plaintext columns, while `national_id` / `passport_number` are encrypted. Patient name + MRN are PHI. Fix: encrypt name/MRN (with blind-index sidecars for search), or document the risk acceptance; align the model's `EncryptedText` usage.
Persona: IT/Security, Compliance.

**M-7 (High) — No role/scope authorization on clinical endpoints.**
`DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]`, `DEFAULT_AUTHENTICATION_CLASSES = []`. 102 of 128 `views.py` set **no** `permission_classes` → any authenticated token (receptionist, patient-portal user, billing clerk) can call ICU, OR, pharmacy-dispensing, lab-results, RCM endpoints. No clinician/nurse/pharmacist/billing RBAC, no purpose-of-use, no per-scope tokens. Fix: role + scope permission classes per module; deny-by-default; separate patient-portal auth from staff auth.
Persona: IT/Security, Compliance.

**M-8 (Medium) — No API rate limiting.**
`DEFAULT_THROTTLE_CLASSES = []`; only website-form scopes have rates. A `platform.security.middleware.RateLimitMiddleware` exists — verify it actually covers `/api/v1/*` and isn't website-only. Fix: default authenticated + anon throttles on the API.
Persona: IT/Security.

**M-9 (Medium) — `settings_local` cannot exercise the live API.**
`CyIdentityAuthMiddleware` always demands an RS256 JWT validated via JWKS (`CYIDENTITY_JWKS_URI`) and ignores `KEYCLOAK_ENABLED`. The documented "local smoke-test" flow can seed + run tests but not call the API without a real Keycloak (this audit patched `_get_jwks_client` to proceed). Fix: a genuine dev-auth shim (like CyCom's `core.dev_auth`) gated on DEBUG + an explicit flag.
Persona: IT, Developer experience.

**M-10 (context) — Auth middleware carries comments documenting three previously-shipped auth defects** ("aud check rejected 100% of real tokens", "campus_ids claim never populated → every campus-scoping check resolved to *sees everything*", "public-path 401s masked by dev shim"). All now patched, but campus-scoping and multi-tenant claim handling warrant targeted regression tests — the pattern ("looked correct in review") recurs.
Persona: IT/Security.

**M-4 (Low) — django.po AR catalog is 96 strings (8 untranslated).**
Matches the tiny template UI. Fine for what's rendered server-side today; will not scale to a real clinical UI. Note as pre-GA.
Persona: Localization.

---

### Workflow / API observations (from the seeded hospital sim: 293 patients, 75 providers, 680 encounters, 2508 orders, 72 admissions, 465 appointments, 12 ICU stays)

- **M-19 (Medium) — Authorization is inconsistent across modules.** `patients`, `encounters`, `clinical/*`, `consents`, `ai-cds/*` are open to any authenticated token; `lab/orders`, `imaging/orders`, `imaging/dicom`, `pharmacy/dispensing`, `pharmacy/interactions` return 403 (some role/feature gate). No coherent RBAC model — it's per-module ad hoc. (Ties M-7.)
- **M-20 (Low) — Seed populates only the acute-care spine.** `rcm/claims`, `careplans`, and several sub-resources are empty, so revenue-cycle, care-planning, blood-bank, and QC workflows could not be exercised end to end. `rcm/kpis` returns the right shape (denial_rate, first_pass_yield, DSO, AR). NPHIES/Hakeem integration apps (`int_nphies`, `int_hakeem`) present but not exercised.
- **M-21 (Low) — `hospital/bed-management/beds/` 404** though the sim created 218 beds — route/path mismatch; bed board not reachable at the obvious path.
- Every seeded patient shares one name ("Dina Al-Masri" / earlier "Sami Mansour") — seed-data quality, not a product defect, but it makes the patient list demo look broken.

## REASONS TO BUY (strengths)

- **Enormous, coherent domain model.** ~140 apps spanning ADT, ICU, OR, ED, nursing, maternity, transfer center, pharmacy (dispensing / compounding / robotics / 340B-style loyalty), lab (accessioning / micro / blood bank / histopath / QC), imaging (PACS / DICOM / teleradiology / AI triage), RCM, ecosystem/referrals, MRFF (ambient scribe, offline kit, population health). The breadth is real and the app boundaries are clean.
- **Right primitives are present:** per-tenant field encryption with blind-index sidecars, an audit hash-chain schema + `verify_chain` tooling, a proper `pharmacy/drug_interactions` engine with override tracking, FHIR R4 scaffolding, consent + break-glass models, CDS risk scores (NEWS2 / sepsis / fall-risk / readmission) that compute correctly.
- **The hospital simulation seeder** produces a realistic acute-care week (ED/clinic/admission mix, ALOS, order volumes) — good for demos and load shaping.
- CDS score endpoints (NEWS2, sepsis) return correct computed results on live data.

---

## EXECUTIVE SUMMARY

CyMed is a very large, well-structured **hospital-ERP backend** — ~140 Django apps with clean domain boundaries and the right security/compliance *primitives* in place. It is **not launch-ready**, and the gaps are not polish items:

1. **It won't install.** A fresh `migrate` does not complete (empty `provider_portal` migrations that tooling silently ignores; an incomplete migration dependency graph). — M-1.
2. **It has no clinician UI.** The only front-end in the repo is 4 Django-templated portal shells + a React Native patient app. No EMR, nurse station, OR board, dispensing screen, or radiology reporting. A hospital cannot run on this as delivered. — M-2.
3. **It keeps no audit trail.** The hash-chained audit sink is fully modelled and has verification tooling, but nothing writes to it — zero PHI-access logging. That is a hard compliance failure (HIPAA/GDPR/NPHIES/Hakeem). — M-11.
4. **PHI protection is fragile and inconsistent.** Encryption key derivation breaks on a non-canonical tenant-UUID string (whole-tenant PHI → HTTP 500); patient name + MRN are stored in plaintext. — M-5, M-6.
5. **Clinical safety checks are stub-grade.** The exposed drug-interaction engine is 6 hardcoded name-matched pairs, does no drug-class allergy cross-check, trusts caller-supplied context over the medical record, and 500s on malformed input. The better engine exists but is gated off. — M-12–M-15.
6. **No coherent authorization.** 102/128 view modules have no permission class; clinical data (incl. bulk national IDs) is readable by any authenticated token; alert overrides are unattributed. — M-7, M-16, M-19.
7. **FHIR is broken** (wrong app labels → 500 on Patient/Observation) and minimal (4 resource types). — M-18.
8. **The safety + security test suites don't run** in a full invocation (collection abort). — M-3.

The distance from here to a pilot is a focused program, not a sprint: make it install, wire the audit sink, fix the crypto key derivation and encrypt names/MRN, converge on the real interaction engine and enable it, add a RBAC layer, and build (or partner for) the clinical UI.

## PRIORITIZED FIX LIST — before any clinical pilot

**Blockers (P0):**
1. **M-1** — fresh `migrate` must complete in one pass; add empty-DB migrate + seed to CI.
2. **M-11** — wire a real hash-chained audit emitter; log every PHI read/write with actor + purpose-of-use.
3. **M-5** — normalise tenant-UUID in `_tenant_dek`; catch `FieldDecryptionError` (no 500s); test all UUID forms derive one DEK.
4. **M-7 / M-19** — deny-by-default RBAC: clinician / nurse / pharmacist / lab / billing / admin roles + scopes on every module; separate patient-portal auth from staff auth.
5. **M-6** — encrypt patient name + MRN (blind-index for search).
6. **M-2** — decide and resource the clinician UI (build vs partner); be explicit with buyers about what ships.

**High (P1):**
7. **M-12–M-15** — converge on `pharmacy/drug_interactions`, enable it, retire the `ai_cds` stub; integrate a real drug-knowledge DB; load allergies/meds server-side; class-based allergy matching.
8. **M-16** — capture the overriding clinician + mandatory reason on every CDS alert override.
9. **M-18** — fix FHIR app-label bugs; add Encounter/Condition/MedicationRequest/AllergyIntolerance/DiagnosticReport/ServiceRequest; conformance test.
10. **M-3** — fix `tests/` collection so the security + clinical-safety suites run; assert a min test count in CI.
11. **M-17** — enforce signature on active consent; validate `policy_rule`; wire consent into data access.
12. **M-9** — real dev-auth shim so the documented local flow can exercise the API.

**Medium (P2):**
13. **M-8** — default API throttles.
14. **M-10** — regression tests for campus-scoping + multi-tenant claim handling.
15. **M-21** — fix the bed-management route; **M-20** — extend the seeder to RCM/care-plans/blood-bank for full-workflow demos.
16. **M-4** — grow the AR i18n catalog alongside the real UI.

## BUYER VERDICT (skeptical hospital IT director)

**Would I buy this today? No.** The ambition and domain coverage are genuinely impressive and the architecture is sound, but I cannot run a hospital on a system that (a) doesn't install cleanly, (b) has no clinician-facing application, (c) keeps no audit log, and (d) ships a toy drug-interaction checker as the exposed one. Those are patient-safety and legal-compliance issues, not feature gaps.

**What would change my answer to yes:** a build that installs from clean in one command; a working audit trail I can hand to a compliance auditor; the real interaction/allergy engine on by default with a licensed drug database behind it; a role model that stops a receptionist from reading ICU notes; and either a delivered clinician UI or a named, credible UI partner with a timeline. Show me those five and a reference site running them, and this becomes a serious contender on breadth alone — very little else on the market covers this much of a hospital in one coherent model.
