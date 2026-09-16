# CyED — ST4S / APP Compliance Mapping

> ## ⚠️ DO NOT SUBMIT THIS TO AN ASSESSOR AS-IS — 2026-08-11
>
> This map states intent. `AUDIT_PROCUREMENT_AND_ST4S_2026-08-11.md` audited the
> same controls against the running code and disagrees on three rows. Where they
> conflict, **the audit is authoritative** — it inverted the burden of proof and
> checked source.
>
> | Row | This map says | Audit found |
> |---|---|---|
> | Zero model training / retention | ✅ built | **NOT EVIDENCED** — no enterprise ZDR contract. `no_train=True` is a local flag, not a term of service. |
> | Encryption at rest (AES-256) | ⚙️ KMS + volume | **Fernet = AES-128-CBC**, not AES-256. Full-disk encryption unverified. |
> | MFA | ⚙️ "enforced at IdP" | TOTP/backup-code/step-up MFA **does exist in `security/`** (22 routes, `test_mfa.py` passing) — so this row understates the code — but IdP-level enforcement for all staff is still not configured or evidenced. |
>
> A ✅ here means "software exists". It does not mean the control is *evidenced*,
> and ST4S assesses evidence. Reconcile this file against the audit before any
> submission.

Maps the Safer Technologies 4 Schools (ST4S, Education Services Australia) checklist
and Australian Privacy Principles (APP) controls to CyED's actual implementation.
**Legend:** ✅ built in code · ⚙️ deployment/config · 🔌 external integration.

## 2. AI & Responsible-AI Governance
| Control | Status | Where |
|---|---|---|
| Zero model training on student data | ✅ | `AgentDefinition.no_train=True`; `llm.py` uses Anthropic API (not a training channel); interactions logged, not retained for training |
| Socratic & safety guardrails (no direct answers) | ✅ | `socratic.py` — guiding-questions-only, `answer_withheld`, `llm.SOCRATIC_SYSTEM_PROMPT`; declines off-curriculum |
| AI data minimisation (strip PII before LLM) | ✅ | `anonymize.py` — redacts names/emails/phones/IDs; wired into `tutor.ask` + `socratic.ask` before any model call |
| Human-in-the-loop oversight | ✅ | `GeneratedArtifact` pending_review → teacher approve/reject; `IntegrityReview.decision` always human; ACARA HITL disclaimer on outputs |
| Grounding / no hallucinated content | ✅ | RAG over `CurriculumOutcome` (ACARA v9); answers cite AC9 codes; refuse when ungrounded |

## 1. Data Residency & Sovereignty
| Control | Status | Where |
|---|---|---|
| Australian onshore hosting | ⚙️ | Deploy to AWS `ap-southeast-2` / Azure Australia East; `TIME_ZONE=Australia/Sydney` |
| Backup sovereignty (APP 8) | ⚙️ | Backup policy / bucket region config |
| Cross-border transfer controls | ⚙️ / ✅ | Anonymisation limits egress PII; egress filtering is infra |

## 3. Authentication & Access Control
| Control | Status | Where |
|---|---|---|
| Identity federation / SSO (OIDC/SAML) | ⚙️🔌 | `CyIdentityAuthMiddleware` validates RS256 JWT via JWKS; wire Entra ID / Google Workspace at the IdP |
| MFA (admin/finance/teacher) | ⚙️ | Enforced at IdP / gateway |
| Granular RBAC | ✅ / ⚙️ | Tenant isolation (`TenantScopedModelViewSet` + `tenant_id`), role claims; per-record field policies to extend |
| Session management | ⚙️ | Token TTL at gateway |

## 4. Encryption & Data Protection
| Control | Status | Where |
|---|---|---|
| Encryption at rest (AES-256) | ⚙️ | Cloud KMS + volume encryption |
| Encryption in transit (TLS 1.3) | ⚙️ | Gateway/ingress |
| Field-level encryption (medical/counselling) | ⚙️ | `WellbeingNote.is_confidential` flags scope; column encryption at DB |
| Biometric template protection | 🔌 | Edge-kiosk hardware (out of scope for core) |

## 6. Audit Logging & Monitoring
| Control | Status | Where |
|---|---|---|
| Comprehensive audit logging | ✅ / ⚙️ | `platform.audit`; `AgentInteractionLog` for every AI call |
| SIEM streaming | ⚙️🔌 | AU-hosted SIEM |
| NDB breach response | ⚙️ | Process/runbook |
| Pen testing / SAST-DAST | ⚙️ | CI pipeline |

## 7. Data Retention, Anonymisation & Deletion
| Control | Status | Where |
|---|---|---|
| Right to erasure / de-identification | ✅ | `POST /api/v1/sis/students/{id}/deidentify/` — strips PII, preserves anonymised stats |
| Data export portability (JSON) | ✅ | `GET /api/v1/sis/students/{id}/export/` — full record for transfer |
| Automated retention schedules | ⚙️ | Cron/management command to add |

## Predictive Student Success (doc §4)
| Control | Status | Where |
|---|---|---|
| At-risk analytics (attendance/grades/behaviour) | ✅ | `analytics/services.py` → `GET /api/v1/analytics/at-risk/`; explainable factors, advisory only |

## Summary
The **AI-governance and data-subject-rights controls that are software** are built and
test-covered in CyED (Socratic guardrails, anonymisation, HITL, grounding, at-risk
analytics, export, de-identification). The remaining items are **deployment/config**
(AU region, KMS, TLS, SSO/MFA, SIEM, retention cron) or **hardware/edge** (biometric
kiosks) — addressed at infrastructure/integration time, not in application code.
