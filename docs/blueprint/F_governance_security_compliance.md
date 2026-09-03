# Section F — Governance, Security & Compliance

## F.1 Governance charter (outline)

### Cross-Domain Architecture Council (CDAC)

**Purpose:** own the canonical data model, API contracts, event schemas, and flavor
standards so the three-product split never returns and flavors stay thin.

| Item | Definition |
|---|---|
| **Members** | Head of Platform (chair), one architect per domain (Commerce, Health, Finance/Compliance, Platform/Infra), Security lead, Product lead. Quorum 4. |
| **Cadence** | Weekly 60-min review; async RFC queue; emergency review on demand (< 24h SLA for prod-blocking). |
| **Decides** | canonical schema changes; new/changed API contracts (major); event schema registry entries; new flavor approval; cross-domain workflow designs; deviations from NFRs; residency/region decisions. |
| **Does not decide** | intra-flavor UX, sprint scope, hiring — those stay with pods. |
| **Instruments** | ADRs (in `docs/adr/`), RFC template, schema registry, API contract repo, `CODEOWNERS` on `platform/` + canonical models + `docs/blueprint/`. |

### Ownership map

| Asset | Owner | Change process |
|---|---|---|
| Canonical data model (`platform/common`, core entities) | Head of Platform | RFC → CDAC approval → expand/contract migration → contract tests |
| API contracts (OpenAPI/GraphQL/AsyncAPI) | Domain architect + API guild | contract-first PR, consumer sign-off, versioned, deprecation policy |
| Event schema registry | Platform architect | additive-only within a major; registry PR + CDAC |
| Flavor definitions | Flavor governance board (subset of CDAC + the owning product pod) | flavor RFC → review against "thin flavor" checklist → versioned release behind flag |
| Security controls | Security lead | policy in `docs/security/`; exceptions time-boxed + logged |
| Regulatory mappings | Finance/Compliance architect + external counsel per country | per-country matrix (F.4), reviewed quarterly + on regulation change |
| Infra / K8s / GitOps | Platform/Infra | IaC PR, staged rollout, change calendar |

### "Thin flavor" checklist (gate for any new flavor)

- [ ] No new top-level model — only `attributes` profiles or typed extension tables reviewed by CDAC.
- [ ] No bespoke frontend — only design-system layout templates.
- [ ] Reuses core services (catalog/orders/inventory/finance/scheduling) unchanged.
- [ ] Tax/regulatory handled by presets, not code branches.
- [ ] Emits standard domain events; no direct cross-flavor table access.
- [ ] Ships with: seed demo, KPI pack, runbook, support playbook, Arabic strings.

### Decision gates (program-level) — see also `J`

MVP-readiness gate · cross-domain-risk gate · regulatory-readiness gate · security gate ·
executive go/no-go per wave. Each gate has an owner, evidence checklist, and a documented
decision in `PROJECT_STATE.md`.

## F.2 Security controls matrix

| Domain | Control | Standard / target | Status today |
|---|---|---|---|
| **Identity** | OIDC SSO, per-tenant realm/federation, service identities | Keycloak; no shared secrets; workload identity | present (CyIdentity); consolidate CyShop JWT |
| **AuthN** | MFA (TOTP + WebAuthn), step-up for high-risk actions | mandatory for admin/finance/PHI roles | built; enforce policy |
| **AuthZ** | RBAC tenant-scoped + ABAC policies for cross-tenant | default-deny; least privilege | present; add policy engine coverage |
| **Tenant isolation** | queryset scoping + Postgres RLS + per-tenant DEK + object prefix | defence-in-depth, all four layers | scoping present; **RLS + per-tenant DEK to build**; cross-tenant read leak fixed in `D:\cybercom` (port it) |
| **Encryption in transit** | TLS 1.3 external + internal (mesh mTLS) | no plaintext hops | external yes; internal mTLS to add |
| **Encryption at rest** | AES-256 DB/object/backup; field-level for ID/Iqama/IBAN/PHI | KMS-managed, per-tenant DEK, annual rotation | to build (ruflo memory encryption also currently off locally) |
| **Secrets** | external secret manager; none in git/images/env | Vault or cloud KMS; CI-injected | compose uses `.env` templates — migrate to secret manager |
| **Audit** | immutable, hash-chained, PII-scrubbed; auth/data/config/finance/PHI events | 7y financial; per-reg health; tamper-evident | `platform/audit` present; add hash-chain + DSAR |
| **App security** | SAST, dependency scan, secret scan in CI; DAST on staging; annual pentest; bug bounty post-GA | block-on-high in CI | cymed has `security-scan.yml` — extend repo-wide |
| **Supply chain** | signed images (cosign), SBOM, pinned deps, base-image patching | provenance attestation | to build in CI |
| **Network** | private subnets, WAF, egress allow-list, no public DB | zero inbound to data tier | to build with K8s |
| **Data residency** | region pinning per tenant; regulated categories never cross border | PDPL; contractual | `residency_region` field to add + enforce at data layer |
| **Backup / DR** | encrypted, in-region, tested restores | RPO ≤ 5 min, RTO ≤ 1h; quarterly restore drill | daemon `backup` worker exists (ops-level); formalise |
| **Incident response** | severity matrix, on-call, comms plan, regulator-notification clock (PDPL 72h) | runbook per alert; blameless postmortem | `PRODUCTION_RUNBOOK.md` exists — extend |
| **AI governance** | model risk classification, human review, auditability | `docs/ai/*` (exists); ModelGateway flagged simulated | wire real gateway under existing governance |
| **Threat modelling** | STRIDE per service at design + each major | `docs/security/THREAT_MODEL.md` extend | present, extend per service |

## F.3 Zero-trust reference (how it applies here)

1. **No network is trusted.** Internal calls authenticated (mTLS or signed short-TTL JWT) and authorised, not just firewalled.
2. **Verify explicitly.** Every request: identity + device/workload posture + tenant scope + policy check.
3. **Least privilege, just-in-time.** Break-glass access is time-boxed, approved, and fully audited (`cyidentity` has break-glass models).
4. **Assume breach.** Segment by tenant + region; encrypt everything; minimise blast radius; detailed telemetry; rehearse IR.
5. **Continuous validation.** Access re-evaluated on risk signals; sessions short; step-up on sensitive actions.

## F.4 Gulf regulatory map (target markets)

### Saudi Arabia (KSA) — priority scale market

| Requirement | Obligation | Implementation |
|---|---|---|
| **ZATCA e-invoicing Phase 2** | Real-time **clearance** of tax invoices via Fatoora; structured XML (UBL 2.1), cryptographic stamp, QR, hash chain. Mandatory for VAT-registered businesses (waves completed through 2026-06-30). | Finance service: XML generator, CSID onboarding, clearance/reporting API client, QR + hash-chain, archival (CyVault). **Net-new, P0 for any KSA tenant.** |
| **VAT** | 15% standard; zero-rated/exempt categories (many foods, healthcare, exports). | TaxRule presets per flavor; reverse-charge for imports/B2B. |
| **PDPL (SDAIA)** | Lawful basis, data-subject rights, breach notification, **data-residency for personal data of KSA residents**; sensitive categories (health, biometric, financial-identity) processed in-Kingdom. | `residency_region` = KSA sovereign region for KSA tenants; DSAR workflow; consent ledger; DPIA per flavor. |
| **Payroll** | GOSI contributions (2026 schedule), **WPS** (Mudad) salary file, Saudization/Nitaqat reporting, end-of-service. | Payroll country profile `SA_GOSI` (coded — confirm flagged rate); WPS SIF generator (to build). |
| **Health (NPHIES)** | Electronic claims/eligibility/pre-auth via NPHIES; provider licensing; SFDA for pharmacy. | HealthFlavour RCM → NPHIES connector; controlled-substance register. |
| **Payments** | SAMA-regulated PSPs; card data → PCI DSS. | Local PSPs (HyperPay, Moyasar, PayTabs); tokenisation; PCI SAQ-A (no card data on our servers). |

### United Arab Emirates (UAE)

| Requirement | Obligation | Implementation |
|---|---|---|
| **E-invoicing** | Federal e-invoicing programme (phased rollout; Peppol-based model). | Finance service pluggable clearance/reporting mode `AE_PEPPOL`; monitor go-live dates. |
| **VAT** | 5% standard; designated-zone rules. | TaxRule presets. |
| **PDPL (Federal) + free-zone regimes (DIFC/ADGM DP laws)** | Consent, DSRs, cross-border transfer controls; some sectors data-local. | residency = UAE region; per-free-zone config flags. |
| **Payroll / WPS** | UAE WPS SIF via agent banks; gratuity (coded — confirm flagged national %); GPSSA for nationals. | Payroll profile `AE_GRATUITY` + WPS SIF generator. |
| **Health** | Emirate-level (DHA Dubai / DoH Abu Dhabi eClaim / Riayati). | HealthFlavour connectors per emirate. |

### Jordan (JO) — beachhead

| Requirement | Obligation | Implementation |
|---|---|---|
| **VAT / GST (ISTD)** | Sales tax; national e-invoicing system (JoFotara) rolling out. | TaxRule presets; `JO_JOFOTARA` clearance mode. |
| **Data protection** | Personal Data Protection Law (2023) — consent, DSRs, controller obligations. | same consent/DSAR machinery; residency default `me-south-1` acceptable for pilot. |
| **Payroll** | Social Security Corporation contributions, income tax. | Payroll profile `JO` (coded). |

### Cross-cutting

| Area | Standard |
|---|---|
| Card payments | **PCI DSS** — architecture keeps card data off our systems (tokenised at PSP); target **SAQ-A**; annual attestation. |
| Infosec certification path | **ISO 27001** (year 1–2), **SOC 2 Type II** for enterprise/health buyers. |
| Health data | country-specific + general "PHI = highest sensitivity" handling (encryption, access audit, minimum necessary, in-region). |
| Accessibility | WCAG 2.2 AA for customer-facing + operator apps. |
| AI | per `docs/ai/` — model risk classification, human-in-loop for clinical/financial decisions, auditability, disclosure. |

## F.5 Compliance operating model

- **Per-country matrix** (above) maintained by Finance/Compliance architect + local counsel; reviewed quarterly and on any regulation change; each row has: obligation, owner, implementation ref, evidence, last-verified date.
- **Flavor regulatory packs**: each flavor declares `regulatory: [...]`; provisioning refuses to activate a flavor in a country where a required pack is not `ready`.
- **Evidence store**: clearance receipts, DPIAs, pentest reports, restore-drill logs, DSAR records — retained per regulation, in CyVault, access-audited.
- **Regulator clocks**: PDPL breach notification (KSA/JO variants), tax filing deadlines — tracked as calendar obligations with alerting.
