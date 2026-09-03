# SOC 2 Type II Readiness — CyMed

Trust Services Criteria (2017) mapping.

## Common Criteria (CC1-CC9)

| CC  | Criterion | Status | Evidence |
|-----|---|---|---|
| CC1 | Control environment / governance | ⚠ | Board charter + code of ethics pending |
| CC2 | Communication & information | ✅ | Runbooks in `docs/ops/`, security policy signed |
| CC3 | Risk assessment | ⚠ | Annual risk register kickoff Q1 |
| CC4 | Monitoring activities | ✅ | Datadog + Sentry + PagerDuty; weekly review meeting |
| CC5 | Control activities | ✅ | PR review 2-approver, SAST in CI, dependabot |
| CC6 | Logical & physical access | ✅ | OIDC MFA + Guardian object perms + LUKS + cloud IAM |
| CC7 | System operations | ✅ | Kubernetes with rolling deploys; incident on-call rotation |
| CC8 | Change management | ✅ | GitOps; Terraform for infra; migrations gated |
| CC9 | Risk mitigation (vendors) | ⚠ | Vendor security questionnaire template pending |

## Additional TSC categories in scope

- **Confidentiality (C1)** — encryption at rest + in transit + field-level pgcrypto for PII
- **Processing Integrity (PI1)** — audit checksums on financial + clinical writes
- **Availability (A1)** — multi-AZ + backup restore drill quarterly
- **Privacy (P1-P8)** — GDPR + HIPAA compliance covers most; explicit privacy notice required

## 12-month audit window

Recommended start date: end of Q1 (allows 3 months evidence buildup pre-window).
Audit firm: to select from Big 4 or specialised (Prescient, Insight Assurance).

## Evidence collection automation

Configure Vanta or Drata to auto-collect:
- HR onboard/offboard events
- Access logs (Guardian + tenant)
- Backup completion
- Vulnerability scan output
- Uptime + SLA metrics
