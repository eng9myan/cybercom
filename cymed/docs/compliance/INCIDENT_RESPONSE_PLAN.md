# CyMed Incident Response Plan

## Definitions
- **Security incident**: unauthorised access, disclosure, modification, or destruction of PHI or business data.
- **Breach**: incident meeting HIPAA/GDPR notification threshold (unsecured PHI or personal data affected).

## Severity levels
| Sev | Trigger | Initial response time |
|-----|---|---|
| SEV-1 | Active PHI exfiltration OR platform down | 15 min |
| SEV-2 | Confirmed vulnerability, contained OR partial outage | 1 hour |
| SEV-3 | Suspected security event, low blast radius | 8 hours |
| SEV-4 | Compliance finding, no PHI risk | 5 business days |

## Response phases

1. **Identify** — via Sentry/Datadog/GuardDuty alert, staff report to `security@cymed.sa`, or bug bounty.
2. **Contain** — revoke tokens, disable affected user/tenant, isolate compromised host.
3. **Eradicate** — patch vuln, rotate secrets, remove attacker persistence.
4. **Recover** — restore from clean backup if needed, monitor closely.
5. **Notify**:
   - Internal: CEO within 1h for SEV-1/2
   - Affected tenants: within 24h with facts, within 72h with breach details (GDPR window)
   - Regulators: HIPAA — 60 days; GDPR — 72h; SFDA/CCHI — per contract
   - Data subjects: without undue delay if high risk
6. **Post-incident**:
   - Blameless PIR within 5 business days
   - Root cause + corrective actions + owner + due date
   - Update runbooks + preventative controls

## Roles

- **Incident Commander** — on-call SRE lead
- **CISO** — legal + regulator liaison
- **DPO** — data-subject notification
- **PR / Comms** — external messaging (SEV-1 only)
- **Legal** — outside counsel for breach cases

## On-call

PagerDuty rotation `cymed-security`. Escalation ladder in `pagerduty.yaml`.

## Breach notification templates

Located in `docs/compliance/notification_templates/`:
- `en_data_subject.md` / `ar_data_subject.md`
- `en_regulator_hipaa.md` / `ar_regulator_pdpl.md`
- `en_customer.md` / `ar_customer.md`

## Simulation cadence

- Tabletop: quarterly
- Full simulation: annually
