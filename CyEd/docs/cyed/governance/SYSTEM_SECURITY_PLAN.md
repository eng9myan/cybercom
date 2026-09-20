# CyEd — System Security Plan (SSP)

**Status: DRAFT — requires the operating school's/reseller's review, region-specific completion, and formal sign-off before submission to any assessor or regulator.** Everything below states what the system actually does, verified against the running code as of 2026-09-20, not aspirational design.

## 1. Purpose and scope

This SSP describes the technical and organisational controls protecting student, staff and family data in CyEd, a multi-tenant school-management platform. It covers the application and its data layer; it does **not** cover network/infrastructure controls (hosting provider, firewall, DDoS protection) or an operator's own physical/office security — those are deployment-specific and must be documented separately by whoever hosts a given tenant.

## 2. System description

- **Architecture**: Django REST backend (`core/`, `products/cyed/*`), Next.js frontend (`cyed-web/`), PostgreSQL. Multi-tenant: every table inherits `tenant_id`.
- **Identity**: JWT bearer tokens verified against an external IdP's JWKS endpoint (`shared/auth` — RS256 signature verification, no locally-issued tokens in production). A `core.dev_auth`-style unsigned-token bypass exists but is hard-gated behind `DEBUG=True` + an explicit env flag; it must never be reachable in a production deployment.

## 3. Data classification

| Class | Examples | Controls |
|---|---|---|
| PHI/PII — health | Allergies, conditions, medications, Medicare numbers, medical-incident detail | Field-level encryption (§4), RLS, role-gated read |
| PII — identity | Name, DOB, address, national/USI identifiers | Field-level encryption on the highest-sensitivity fields (national ID, passport-equivalent), RLS |
| PII — academic | Grades, attendance, behaviour records | Tenant + role scoping, audit trail on read/write |
| Financial | Fee invoices, payroll, bank statements | Role-gated (finance/leadership), step-up MFA on state-changing actions (§5) |
| Operational | Visitor logs, late passes | Tenant-scoped, time-limited retention (§7) |

## 4. Encryption

- **At rest, field-level**: `core/crypto.py`. Active cipher is **AES-256-GCM** (`AESGCM`, 96-bit nonce, unique per encryption), keys derived via `HKDF-SHA256` to a genuine 256-bit key regardless of input key material. Version-tagged ciphertext (`enc:v2:`) so historical rows encrypted under the prior Fernet/AES-128-CBC scheme (`enc:v1:`) remain readable without a forced re-encryption migration. Multi-key rotation supported (new writes use the newest key; reads try all configured keys).
- **Key management**: key material is supplied via environment variable (`CYED_FIELD_KEY`) at deploy time. **Gap**: no KMS/envelope-encryption integration exists yet — an operator using a cloud KMS (AWS KMS, Azure Key Vault) for envelope wrapping must add that layer themselves; this SSP will be updated when it lands in the product.
- **At rest, disk/database**: infrastructure-level (cloud-provider EBS/managed-Postgres encryption). **Not verifiable from the application** — the hosting operator must document and attach evidence (e.g. an AWS/Azure encryption-at-rest configuration export) separately.
- **In transit**: TLS is a gateway/ingress responsibility, not application code. The application sets `SECURE_HSTS_SECONDS`, secure cookies, and `Strict-Transport-Security` headers in production settings; actual TLS termination and certificate management is the hosting operator's.

## 5. Authentication and access control

- **RBAC**: role claims carried in the JWT (`realm_access.roles`), checked per-endpoint (`IsStaff`, `IsFinanceOrLeadership`, `CLINICAL_STAFF_ROLES`-equivalent patterns, etc. — see `products/cyed/governance/access.py`).
- **Row-level scoping**: parents/students see only their own/their children's records (`scope_queryset_by_student`); campus-bound staff are scoped to their campus (`CampusScopedMixin`).
- **Database-layer defence in depth**: PostgreSQL Row-Level Security (`FORCE ROW LEVEL SECURITY` + a `tenant_isolation` policy) on sensitive tables, keyed on `current_setting('app.current_tenant_id')`, set per-request via `ATOMIC_REQUESTS` — a bug in application-layer tenant filtering does not by itself leak data across tenants.
- **MFA**: RFC 6238 TOTP + 10 single-use backup codes, lockout after 5 failed attempts in 15 minutes, append-only `SecurityEvent` log (`products/cyed/security/`). **Step-up MFA** (`RequiresRecentMfa`, a 15-minute freshness window) is enforced on the highest-stakes state-changing actions: marking a payroll run/payslip paid, approving a budget, finalising a bank reconciliation. Enrollment is currently **opt-in for general staff, effectively mandatory for anyone performing the actions above** (they cannot complete those actions without enrolling — the permission fails closed). **Gap**: no login-flow gate forces MFA enrollment for every staff account regardless of role; enforcing that at account provisioning/IdP level is an operator decision, not yet built into this codebase.

## 6. Audit logging

- `AuditEvent` (`products/cyed/governance/models.py`): append-only, no API path exists to update or delete a row (WORM). Records actor, role, action (create/update/delete/sensitive-read), model, object id, summary. Written automatically by `AuditedTenantViewSet`-based views on sensitive models (student PII, grades, wellbeing/health) and explicitly by the security-relevant actions above.
- `SecurityEvent` (`products/cyed/security/models.py`): MFA enrollment, verification, lockout, and step-up-denied events.
- `SignatureAuditEvent` (`products/cyed/docsign/models.py`): every send/view/sign/decline/void of a signable document (contracts, permission slips), with actor, timestamp, IP.

## 7. Retention and disposal

Formalised in `products/cyed/governance/retention.py` and the companion `DATA_RETENTION_SCHEDULE.md`. `python manage.py run_retention_sweep` (dry-run by default) de-identifies long-departed students and purges stale visitor logs and unsuccessful admissions applications, each action logged to `AuditEvent`. Intended to run on a schedule (cron/CronJob) — **the operator must actually schedule it**; this codebase provides the mechanism, not a running cron job.

## 8. Third-party / AI processing

- AI tutoring (`products/cyed/ai_agents/`) strips PII (`anonymize.py`) before any call to the underlying model provider, and enforces Socratic (guiding-questions-only) responses for students plus human-in-the-loop review of generated artefacts.
- **Gap**: no enterprise Zero Data Retention (ZDR) contract with the model provider is evidenced. Anonymisation reduces but does not eliminate the exposure of a third-party model call; a school handling this as a compliance-sensitive question should either obtain ZDR terms or move inference to a self-hosted/onshore model before relying on the AI features for real student data under a strict data-sovereignty mandate.

## 9. Known gaps (do not represent these as resolved)

1. SIF AU v3.x: RefId registry and 5 core object mappers exist and are tested; NAPLAN/NCCD/STATS statutory exports are **not yet** wrapped as SIF-conformant payloads (still bespoke CSV/JSON).
2. Data sovereignty (APP 8): no region-pinning or sub-processor register exists in the application; entirely an infrastructure/contract matter for the operator.
3. Independent penetration test and formal ST4S assessment: not commissioned as of this document's date.
4. KMS envelope encryption for field-level keys: not integrated (see §4).

## 10. Review

This document should be reviewed whenever a control listed above changes, and at minimum annually. Owner: ______________________. Last technical accuracy check: 2026-09-20 (against the running codebase, not a design document).
