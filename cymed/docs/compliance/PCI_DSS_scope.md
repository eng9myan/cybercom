# PCI DSS Scope + Attestation Route — CyMed

## Current model: Router (Model B)

Patient pays directly to provider's merchant account via HyperPay / Checkout / Stripe / STC Pay / CliQ redirect + hosted fields. CyMed **never** stores or transmits primary account number (PAN), track data, or CVV.

- **Merchant of record:** the provider tenant.
- **PAN storage:** none. Gateway returns opaque token.
- **CVV storage:** none.
- **Cardholder data flow:** browser → gateway hosted fields → gateway → CyMed receives token only.

**Attestation level:** SAQ A (SAQ A eligibility as service provider only handling redirected checkout).

## Future model: Aggregator (Model A)

Requires **PCI DSS Level 1** attestation + SAMA Open Banking licensing. Target Q3.
Adds direct cardholder data envelope + tokenisation service inside CyMed VPC.

## Controls in place today

| Requirement | Control |
|---|---|
| Req 1 (firewall) | Cloud security groups + WAF |
| Req 2 (defaults) | Terraform baselines strip all defaults |
| Req 3 (protect stored data) | Gateway tokens only; no PAN ever stored |
| Req 4 (encrypt transmission) | TLS 1.3 minimum; HSTS everywhere |
| Req 5 (anti-malware) | Container base images scanned; distroless where possible |
| Req 6 (secure development) | SAST + SCA in CI, code review required |
| Req 7 (access) | Guardian + tenant RLS + MFA |
| Req 8 (identify + auth) | OIDC + WebAuthn |
| Req 9 (physical) | Cloud provider |
| Req 10 (log + monitor) | `platform.audit` + Datadog + immutable log store |
| Req 11 (test regularly) | Annual pen-test + quarterly vuln scan |
| Req 12 (policy) | This document set |

## Attestation route

- **Now:** self-attestation SAQ A signed by CISO.
- **Q3 (Aggregator upgrade):** engage QSA (Coalfire / SecurityMetrics), ~$40-60K first year, ~$25K annual.
