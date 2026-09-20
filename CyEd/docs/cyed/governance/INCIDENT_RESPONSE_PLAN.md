# CyEd — Incident Response Plan (IRP)

**Status: DRAFT — the operating school/reseller must fill in the bracketed contacts, confirm the 72-hour OAIC notification clock against current Australian Privacy Act obligations at the time of an actual incident, and formally adopt this plan before relying on it.**

## 1. Purpose

Defines how CyEd (the product operator) and a school (the data controller for its own students' records) respond to a suspected or confirmed data breach or security incident, consistent with the Notifiable Data Breaches (NDB) scheme under the Australian Privacy Act.

## 2. Roles

| Role | Responsibility | Contact |
|---|---|---|
| Incident Lead | Owns the response end-to-end, declares severity | [_____________] |
| Technical Lead | Contains the incident, gathers forensic evidence | [_____________] |
| Privacy Officer / DPO | Assesses notification obligations, liaises with OAIC | [_____________] |
| School Principal / Leadership | Approves guardian/staff communications | [_____________] |
| Communications | Drafts and sends notifications | [_____________] |

## 3. Detection sources

- Application signals already in place: `SecurityEvent` lockouts and step-up denials (`products/cyed/security/`), `AuditEvent` anomalies (e.g. a sensitive-read pattern outside normal hours), failed-login spikes.
- External: hosting-provider alerts, a report from a parent/staff member, a responsible-disclosure report.

**Gap this plan flags, not resolves**: no automated alerting/SIEM currently watches these signals for anomalies — a human must be looking, or the operator must wire one up. This is infrastructure, not application code.

## 4. Severity classification

| Level | Definition | Example |
|---|---|---|
| Critical | Confirmed unauthorised access to PII/PHI at scale, or ongoing active compromise | Database credential leak, ransomware |
| High | Confirmed unauthorised access to a small number of records, or a serious control failure | One account compromised and used to read other students' health records |
| Medium | Suspected but unconfirmed breach, or a vulnerability found before exploitation | A misconfigured permission discovered in review, no evidence of use |
| Low | Policy violation with no PII exposure | An internal audit-log gap |

## 5. Response steps

1. **Detect & triage** — confirm the incident is real, classify severity (§4).
2. **Contain** — for a compromised account: revoke sessions (delete/expire the account's tokens at the IdP), rotate the `CYED_FIELD_KEY` if key material itself may be compromised (this invalidates nothing already encrypted — old ciphertext stays readable under the rotated-in key per `core/crypto.py`'s multi-key design, but a genuinely compromised key must still be retired from `HKDF` derivation going forward). For a database-level compromise: engage the hosting operator's own incident process.
3. **Assess scope** — query `AuditEvent`/`SecurityEvent` for the affected account/window to determine what was actually read or changed. `AuditEvent` rows cannot have been altered after the fact (WORM) — this record is trustworthy evidence.
4. **Eradicate** — patch the root cause (code fix, config fix, credential rotation).
5. **Notify** — see §6.
6. **Recover** — restore normal operation, confirm no residual access.
7. **Post-incident review** — root cause, timeline, what monitoring would have caught it sooner, action items with owners and dates.

## 6. Notification obligations (NDB scheme)

- An eligible data breach (likely to result in serious harm) must be notified to OAIC and affected individuals **as soon as practicable**, and the statutory assessment period is capped at **30 days** from when the entity became aware — do not treat 30 days as a target, treat it as the outer limit; a Privacy Officer should aim to conclude the assessment well inside it.
- Content of a notification (individuals): what happened, what data was involved, what the school/operator is doing, what the individual should do (e.g. change a password), and contact details for questions.
- School students are minors: notification to guardians, not directly to the student, unless the school's own policy and the student's age make direct notification appropriate.
- Log every notification sent (who, when, what) — this itself becomes part of the `AuditEvent`/incident record.

## 7. Evidence handling

- `AuditEvent` and `SecurityEvent` exports for the incident window should be pulled and stored outside the live system (a compromised system's own logs are not trustworthy for long-term evidence retention).
- Do not delete or "clean up" affected records before the assessment is complete — that destroys the evidence needed to assess scope and satisfy any regulator inquiry.

## 8. Testing this plan

This IRP should be tabletop-exercised at least annually. Not yet exercised as of this document's date — schedule the first exercise as part of adopting this plan.

## 9. Review

Owner: ______________________. Last technical accuracy check: 2026-09-20.
