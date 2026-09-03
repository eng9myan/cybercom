# HIPAA Security Rule Compliance Checklist — CyMed

Mapping 45 CFR § 164.308 / 310 / 312 controls to CyMed code paths.
Fill status: ✅ implemented · ⚠ partial · ❌ gap.

## § 164.308 Administrative Safeguards

| # | Control | Status | Evidence |
|---|---|---|---|
| a(1)(ii)(A) | Risk analysis | ⚠ | `docs/compliance/RISK_ASSESSMENT.md` (to write) |
| a(1)(ii)(B) | Risk management | ⚠ | Risk register in Linear project SEC-RISK |
| a(1)(ii)(C) | Sanction policy | ❌ | HR to draft |
| a(1)(ii)(D) | Info system activity review | ✅ | `platform.audit` middleware logs every request |
| a(3) | Workforce security | ⚠ | RBAC via Django Guardian in `platform.cyidentity`; annual training missing |
| a(4) | Info access management | ✅ | `platform.tenant` RLS + Guardian per-object perms |
| a(5)(ii)(D) | Password management | ✅ | Django password hasher argon2 + rotation policy in CyIdentity |
| a(6) | Security incident procedures | ⚠ | `INCIDENT_RESPONSE_PLAN.md` drafted |
| a(7) | Contingency plan | ⚠ | Backups + DR runbook `docs/ops/DR.md` (to write) |
| a(8) | Evaluation (periodic) | ⚠ | Annual pen-test + quarterly self-assessment planned |
| b(1) | Business Associate contracts | ❌ | `BAA_TEMPLATE.md` in progress |

## § 164.310 Physical Safeguards

| # | Control | Status | Evidence |
|---|---|---|---|
| a(1) | Facility access controls | ✅ | Cloud host (AWS/GCP) — inherit SOC 2 |
| b   | Workstation use policy | ⚠ | HR policy pending |
| c   | Workstation security | ⚠ | MDM required — IT to configure |
| d(1) | Device & media controls | ✅ | Mobile app blocks screenshots on PHI screens (spec P0-1 §8) |

## § 164.312 Technical Safeguards

| # | Control | Status | Evidence |
|---|---|---|---|
| a(1) | Access control (unique user ID) | ✅ | `platform.cyidentity.User` + OIDC via Keycloak |
| a(2)(i) | Automatic logoff | ✅ | JWT expiry + Flutter session inactivity timer |
| a(2)(ii) | Encryption/decryption (at rest) | ✅ | Postgres `pgcrypto` for PHI fields + host-level LUKS |
| a(2)(iv) | Encryption in transit | ✅ | TLS 1.3 enforced at reverse proxy + mTLS on payer bridges |
| b   | Audit controls | ✅ | `platform.audit` — every write logged with user, tenant, IP, timestamp |
| c(1) | Integrity | ✅ | Row-level checksums on `patient_portal.NFCScanLog` + `payments.PaymentTransaction` |
| c(2) | Person/entity authentication | ✅ | OAuth2 + WebAuthn biometric (spec P0-1 §2) |
| d(1) | Person authentication (bio) | ✅ | `local_auth` Flutter + WebAuthn |
| e   | Transmission security | ✅ | HTTPS everywhere; NPHIES/JoFotara/Hakeem use mTLS |

## PHI data-flow diagram

Documented in `docs/compliance/DATA_FLOW.md`. Every PHI-touching module
labeled with its trust boundary + encryption state.

## Next actions (30-day sprint)

1. Draft missing docs: RISK_ASSESSMENT · BAA_TEMPLATE · SANCTION_POLICY · WORKSTATION_USE
2. Enable pgcrypto on `patients.Patient` PII columns.
3. Schedule external pen-test window (Q1 wk 8).
4. Annual security awareness training kick-off — all staff by wk 12.
