# External Penetration Test — Scope + Cadence

## Scope

| Domain | Included |
|---|---|
| Web / REST API | `api.cymed.sa/*`, `api.cymed.jo/*` — all versions |
| FHIR R4 server | `/fhir/R4/*` |
| Patient App PWA | `/patient-app/*` shell + service worker |
| Mobile apps | iOS + Android (dynamic analysis, static via MobSF) |
| NFC scan flow | Physical card + terminal token exchange |
| Payment webhooks | HyperPay + Checkout + Stripe + STC Pay + CliQ |
| NPHIES bridge | mTLS handshake + FHIR payload |
| Hakeem bridge | VistaRPC + SFTP paths |
| Admin dashboards | `/dashboard/*`, `/provider-portal/*` |

## Out of scope

- Underlying cloud provider (SOC 2 inherited)
- Third-party payer FHIR servers
- Third-party insurer clearinghouses
- Physical premises (contracted separately)

## Test types

- **Black-box** — external attacker, no credentials
- **Grey-box** — authenticated as patient, staff, admin (one account each)
- **White-box** — code review of new modules only (payments, ai_cds, rcm, nphies, hakeem, fhir_r4)

## Cadence

- Full test: annually.
- Regression retest: after every major release.
- Targeted retest: after any critical finding fix (max 30 days).

## Findings SLA

| Severity | Fix window |
|---|---|
| Critical | 24 hours |
| High | 7 days |
| Medium | 30 days |
| Low | 90 days |
| Info | Next release |

## Deliverables

- Executive summary
- Detailed findings + PoC + reproduction steps
- Remediation guidance
- CVSS 3.1 scores
- Retest report

## Preferred vendors

Rotate every 2-3 years to avoid blind spots: NCC Group · Bishop Fox · Trustwave · Cure53 · Positive Technologies.
