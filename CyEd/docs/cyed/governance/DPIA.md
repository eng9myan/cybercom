# CyEd — Data Protection Impact Assessment (DPIA)

**Status: DRAFT.** A DPIA should be completed (or reviewed and re-signed-off) by the operating school's Privacy Officer/DPO before the assessed features go live with real student data, and re-assessed whenever a covered feature changes materially. This document assesses risk against the platform **as it exists** as of 2026-09-20; it is not a design proposal.

## 1. Purpose and scope

Assesses privacy risk for CyEd's highest-risk processing activities: (a) AI-assisted student tutoring, (b) health/wellbeing record processing, (c) statutory government reporting, (d) automated data retention/disposal.

## 2. Necessity and proportionality

Each activity below is necessary to core school operation (teaching, duty of care, legal compliance) or explicitly optional/opt-in (AI tutoring). None of the processing described exceeds what is needed for its stated purpose — this assessment exists to confirm that, not to justify scope creep.

## 3. Processing activity: AI-assisted tutoring

- **What happens**: a student's question, and relevant curriculum context, is sent to a third-party LLM provider to generate a Socratic (guiding-questions) response.
- **Data involved**: student's question text (which may incidentally contain identifying detail typed by the student), curriculum metadata.
- **Mitigations already built** (`products/cyed/ai_agents/anonymize.py`): names, emails and phone numbers are stripped from the prompt before it leaves the system. The response is constrained to guiding questions, never a direct answer to an assessed task (`socratic.py`). Every AI-generated artefact used for anything beyond a live chat response lands in a `pending_review` queue — a teacher, not the model, is the final authority (human-in-the-loop).
- **Risks**:
  - *Residual re-identification*: anonymisation strips known-format PII (name/email/phone) but cannot catch a student typing something identifying in free text (e.g. "my mum said..."). **Risk: medium, likelihood: low-medium, impact: low** (a single incidental disclosure to a model provider, not a systemic leak).
  - *Third-party retention*: no enterprise Zero Data Retention (ZDR) agreement is evidenced with the model provider. **Risk: medium** — anonymised prompts may still be retained by the provider under its standard terms. **This is the single largest gap in this processing activity.**
- **Recommended mitigation** (not yet actioned): obtain enterprise ZDR terms from the model provider, or move inference to a self-hosted/onshore model, before enabling AI tutoring for students where the school has made data-sovereignty or non-retention commitments to families. Until then, treat this feature as **not compliant** with a strict "no third-party retention" promise, even though anonymisation is real and tested.

## 4. Processing activity: health and wellbeing records

- **What happens**: allergies, conditions, medications, Medicare-equivalent numbers, medical incident narratives, and wellbeing/behaviour notes are recorded for duty-of-care purposes.
- **Mitigations already built**: field-level AES-256-GCM encryption on the specific sensitive fields (allergies, conditions, medications, Medicare number, incident description/treatment, wellbeing notes), role-gated access (health/pastoral/leadership roles only), Row-Level Security as a database-layer backstop, full audit trail on read of sensitive records (`AuditedTenantViewSet`).
- **Risks**: standard insider-misuse risk (a staff member with legitimate role access reading a record without a legitimate reason) is mitigated by the audit trail (detectable after the fact) but **not prevented in real time** — there is no anomaly-detection alerting on unusual read patterns. **Risk: low-medium, impact: high if it occurs** (health data is highly sensitive), likelihood low given RBAC scoping.
- **Recommended mitigation** (not yet actioned): periodic manual review of `AuditEvent` sensitive-read logs by the Privacy Officer, or an automated alert on an unusual volume of sensitive reads by one account.

## 5. Processing activity: statutory government reporting (NCCD, NAPLAN, census)

- **What happens**: de-identified/aggregated and, for NCCD, identified disability-category data is exported for lodgement with government authorities.
- **Mitigations already built**: exports are role-gated (leadership/office only), every export run is logged to `StatutoryReportLog`, NCCD records are unique-per-student-per-collection-year (no duplicate submission drift).
- **Risks**: exports are bespoke CSV/JSON, not SIF-conformant payloads (a SIF RefId registry and 5 core object mappers exist, but NAPLAN/NCCD/STATS specifically are not yet SIF-wrapped) — this is an interoperability gap, not directly a privacy risk, but it does mean a government endpoint expecting SIF cannot machine-consume these exports without a manual translation step, which itself is a point where data could be mishandled outside the platform's own controls. **Risk: low as a direct privacy risk, but a real operational/compliance gap.**

## 6. Processing activity: automated retention/disposal (`run_retention_sweep`)

- **What happens**: de-identifies long-departed students and purges stale visitor logs/unsuccessful applications on a schedule.
- **Mitigations already built**: dry-run by default (nothing acts without an explicit `--apply`), every action logged to `AuditEvent`, tenant-scoped, irreversible action (de-identification) only ever applied to the same operation already exposed as a manual, deliberate staff action elsewhere in the product.
- **Risks**: an incorrectly configured retention window (too short) could de-identify a record a school still needed — mitigated by dry-run-first design, but the *decision* of what window is correct is a school/legal judgement this document cannot make for you. **Risk: low given the safety mechanism, but the consequence of a misconfigured window is irreversible** (de-identification cannot be undone) — treat any change to `RETENTION_POLICIES` as requiring sign-off, not a routine config edit.

## 7. Overall determination

**Conditionally acceptable** for a school that: (a) does not require a strict no-third-party-model-retention guarantee for its AI tutoring feature until ZDR terms are obtained (§3), (b) has assigned someone to periodically review sensitive-read audit logs (§4), and (c) treats retention-window changes as a governed decision, not routine config (§6). **Not yet acceptable** for a school whose compliance posture requires ZDR-or-onshore-model AI processing as a hard requirement — disable AI tutoring for that school until §3's mitigation is actioned.

## 8. Sign-off

| Role | Name | Date | Decision |
|---|---|---|---|
| Privacy Officer / DPO | | | |
| Technical lead | | | |
| Principal / Leadership | | | |

## 9. Review

Re-assess whenever a covered processing activity changes materially, and at minimum annually. Last technical accuracy check: 2026-09-20.
