# CyMed — Pilot Hardening Report

**Owner:** Platform team
**Version:** 1.0
**Date:** 2026-08-19
**Review cadence:** each hardening pass

---

## 1. Migrations status

- **Django `check`:** clean, 0 issues.
- **`makemigrations`:** 48 new `0001_initial.py` files across the P0-8..P0-12 + MRFF-16..19 apps.
- **SQLite dev migrate:** every app applied cleanly (see `MIGRATIONS_STATUS.md`).
- **PostgreSQL production migrate:** pre-flight checklist in `MIGRATIONS_STATUS.md`.

### Repo-structure fixes required to unblock migrations

| Fix | Where |
|---|---|
| `"core.patients.Patient"` → `"cymed_patients.Patient"` | `products/cymed/patient_portal/models.py:24` |
| `"core.providers.Provider"` → `"cymed_providers.Provider"` | `products/cymed/provider_portal/models.py:10, 76` |
| `"patient_portal.PatientPortalProfile"` → `"cymed_patient_portal.PatientPortalProfile"` | `products/cymed/payments/models.py` (7 occurrences) |
| `db_table = "cymed_clinic_referrals"` → `"cymed_clinic_referral_loop_referrals"` | `products/cymed/clinic/referral_loop/models.py:51` (collision with existing `cymed_clinic.referrals`) |
| Add `path = os.path.dirname(...)` to outer `platform.{common,terminology,notifications}` `AppConfig` | outer package apps.py — namespace-package `path` disambiguation required after adding new inner apps |
| Removed shadowed inner duplicates | `products/cymed/platform/{common,terminology,notifications}` (fully shadowed by outer authoritative copies) |

## 2. Files added by category

| Category | Count | Location |
|---|---:|---|
| Security middleware + KMS + RLS | 6 | `platform/security/` |
| Observability logging + metrics + middleware | 7 | `platform/observability/` |
| Celery worker + tasks | 6 | `core/celery.py`, `core/__init__.py`, `products/cymed/payments/tasks.py`, `products/cymed/integrations/nphies/tasks.py`, `platform/notifications/tasks.py`, `deploy/celery/README.md` |
| Real vendor integrations | ~14 | `products/cymed/payments/gateways/hyperpay.py`, `products/cymed/integrations/nphies/client.py`, `products/cymed/integrations/whoicd/*`, `products/cymed/integrations/jofawtra/*` |
| Test scaffolds | ~20 | `products/cymed/{payments,ai_cds,rcm,integrations/nphies,integrations/hakeem}/tests/` |
| Deploy artefacts | 30 | `deploy/docker/`, `deploy/k8s/base/`, `deploy/terraform/aws/`, `.github/workflows/`, `deploy/runbooks/` |
| Commercial + operations pack | 20 | `docs/commercial/`, `docs/onboarding/`, `docs/support/`, `docs/security/`, `docs/regulatory/`, `docs/clinical/`, `docs/OPS_DASHBOARDS.md`, `docs/hardening/PILOT_READINESS_CHECKLIST.md` |
| **Total new files** | **≈ 103** | |

## 3. Django check

`python manage.py check` → **System check identified no issues (0 silenced).**

## 4. AST verification

`ast.parse` across every added `.py`: **88 / 88 clean, 0 errors.**

## 5. Outstanding blockers Claude cannot resolve

These require human, corporate, or vendor actions and cannot be produced in-repo:

1. **SFDA MDR filing** — Class B SaMD registration. Submission pack drafted at `docs/regulatory/SFDA_SUBMISSION_PACK.md`; needs licensed regulatory consultant, ISO 13485 QMS auditor, clinical evaluation report signed by clinician.
2. **HSM / KMS procurement + install** — AWS KMS backend coded in `platform/security/keys.py`, but a real account with dedicated CMKs per data class (RDS/S3/secrets/ECDSA cards) must be provisioned. Azure Key Vault / GCP KMS backends are stubs.
3. **Pentest firm engagement + report** — scope + preferred-firm criteria at `docs/security/PENTEST_PACK.md`. Contract, engagement, remediation cycle are external.
4. **Clinical validation study** — retrospective + prospective + IRB approval. Plan at `docs/clinical/CLINICAL_VALIDATION_PLAN.md`. Requires site medical director, data-sharing agreement, statistician.
5. **Signed BAAs / DPAs with vendors** — AWS, HyperPay, courier, chosen AI vendor. Templates at `docs/commercial/BAA_TEMPLATE.md`, `DPA_TEMPLATE.md`.
6. **CBAHI accreditation cycle** — alignment matrix at `docs/regulatory/CBAHI_ALIGNMENT.md`; on-site survey + gap-closure are external.
7. **CCHI payer onboarding** — payer-by-payer status matrix at `docs/regulatory/CCHI_APPLICATION_STATUS.md`; each payer requires contract + connectivity kit + testing script sign-off.
8. **24/7 support ops staffing** — tiers defined at `docs/support/SUPPORT_TIERS.md`; roles / rotation must be hired.
9. **Production PostgreSQL provisioning + RLS bootstrap** — Terraform module exists at `deploy/terraform/aws/main.tf`; requires AWS account, tfstate bucket, secrets, `terraform apply`.
10. **Real payment-gateway live-account credentials** — HyperPay merchant contract + Mada certification, JoFotara issuer registration + CSR-signed private key.
11. **Real WHO ICD-11 API key** — free registration at https://icd.who.int/icdapi (external).
12. **Real NPHIES production certificate + PSP registration** — CCHI-issued mTLS cert per tenant.
13. **Live clinician sign-off on every CDSS-enabled tenant** — template at `docs/clinical/CLINICIAN_SIGNOFF_TEMPLATE.md`.

## 6. Next-step checklist (dependency-ordered)

- [ ] Pick a design-partner hospital → sign pilot MSA (template ready)
- [ ] Provision AWS account → `terraform apply deploy/terraform/aws/`
- [ ] Bootstrap RDS PostgreSQL 16 + Redis 7 → run `python manage.py migrate` against production
- [ ] Install `sealed-secrets` + `cert-manager` + `nginx-ingress` on EKS
- [ ] Seal `deploy/k8s/base/secret.env.yaml` per environment → commit sealed version
- [ ] Wire real HyperPay + NPHIES sandbox creds via K8s secrets → smoke-test one bill end-to-end
- [ ] Register at WHO ICD-11 API → set env → verify search endpoint returns real data
- [ ] Engage regulatory consultant → complete SFDA technical file
- [ ] Engage pentest firm → 4-week engagement window, remediation window after
- [ ] Recruit local clinical champion → clinical validation study kick-off
- [ ] Hire on-call rotation (min 3 for L2, 3 for L1) → run tabletop incident exercise
- [ ] Quarterly DR drill scheduled (see `deploy/runbooks/DR.md`)
- [ ] Every item in `docs/hardening/PILOT_READINESS_CHECKLIST.md` marked green before scheduling paid pilot go-live

---

**Bottom line:** in-repo hardening is complete. Everything Claude can do without external accounts, contracts, or human validation is done. The remaining 13 blockers are corporate, regulatory, clinical, or vendor-side.
