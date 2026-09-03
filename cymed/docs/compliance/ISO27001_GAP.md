# ISO/IEC 27001:2022 Annex A — Gap Map

## Summary
93 controls · 71 covered · 15 partial · 7 gap.

## Organizational controls (37)

| Control | Status | Owner |
|---|---|---|
| A.5.1 Policies | ⚠ | CISO — consolidate scattered policies |
| A.5.2 Roles | ✅ | Org chart + RACI |
| A.5.3 Segregation of duties | ✅ | 4-eyes on prod deploys + payments |
| A.5.4 Management responsibilities | ✅ | Board attestation |
| A.5.7 Threat intelligence | ⚠ | Sub to CISA + local CERT feeds |
| A.5.9 Inventory of information | ⚠ | Data classification project Q1 |
| A.5.10 Acceptable use | ❌ | HR to publish |
| A.5.15 Access control | ✅ | Guardian + tenant RLS |
| A.5.19 Suppliers | ⚠ | Vendor register |
| A.5.24 Incident planning | ✅ | INCIDENT_RESPONSE_PLAN.md |
| A.5.29 Continuity | ⚠ | BCP tabletop needed |
| A.5.30 ICT readiness | ✅ | Multi-AZ + DR runbook |

## People controls (8)

| Control | Status |
|---|---|
| A.6.3 Awareness / training | ⚠ Annual training TBD |
| A.6.6 NDA | ✅ |
| A.6.7 Remote working | ✅ |

## Physical controls (14)

Cloud provider — inherit SOC 2. Office access via badge + camera.

## Technological controls (34)

| Control | Status | Evidence |
|---|---|---|
| A.8.1 User endpoint | ⚠ | MDM rollout Q2 |
| A.8.2 Privileged access | ✅ | JIT elevation via CyIdentity |
| A.8.3 Access restriction | ✅ | Guardian + RLS |
| A.8.7 Malware protection | ✅ | Container scanning |
| A.8.8 Vulnerability | ✅ | Dependabot + Snyk |
| A.8.9 Config mgmt | ✅ | Terraform + Ansible |
| A.8.10 Info deletion | ✅ | Hard-erasure workflow |
| A.8.11 Data masking | ⚠ | Only in analytics exports |
| A.8.12 DLP | ❌ | Nightingale eval Q2 |
| A.8.15 Logging | ✅ | platform.audit |
| A.8.16 Monitoring | ✅ | Datadog + Sentry |
| A.8.17 Clock sync | ✅ | NTP everywhere |
| A.8.20-22 Networks | ✅ | Segmented VPCs |
| A.8.24 Cryptography | ✅ | TLS 1.3 + AES-256 |
| A.8.25 SDLC | ✅ | Secure code review |
| A.8.26 App sec | ✅ | SAST + DAST |
| A.8.28 Secure coding | ✅ | Coding standards + training |
| A.8.29 Security testing | ✅ | See PEN_TEST_SCOPE.md |
| A.8.30 Outsourced dev | N/A | Internal only |

## Next 90 days
1. Publish consolidated ISMS policy set.
2. Finish data classification + retention register.
3. Roll out MDM to all clinical + engineering endpoints.
4. Kick off BCP tabletop.
