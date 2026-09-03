# CyMed Threat Model — STRIDE per Trust Boundary

| Field | Value |
|---|---|
| Version | 0.1 (Draft) |
| Date | 2026-08-19 |
| Owner | `<CISO / Head of Security — TBD>` |
| Review cadence | Per release, at minimum semi-annually |

---

## 0. Scope and method

Scope: the CyMed platform in production; edges where trust changes. Method: STRIDE (Spoofing, Tampering, Repudiation, Information disclosure, Denial of Service, Elevation of privilege), applied per trust boundary. Each row maps a threat to its principal mitigation and the code paths / configuration that implement it. Paths use forward slashes and are relative to `D:/cybercom/cymed/`.

## 1. Trust boundaries in scope

1. **Mobile app** (patient / caregiver) ↔ API gateway.
2. **Patient portal (web)** ↔ API gateway.
3. **Provider portal (web/desktop)** ↔ API gateway.
4. **Admin / control plane** ↔ management API.
5. **NPHIES bridge** ↔ external national exchange.
6. **Payment gateway** integration.
7. **Image-share links** (external, time-boxed, patient-shareable).
8. **DICOM ingress** (modalities and referring PACS).

Cross-cutting: internal service ↔ service (mTLS); DB ↔ services; secrets ↔ services.

---

## 2. Mobile app ↔ API gateway

| # | STRIDE | Threat | Mitigation | Code / config |
|---:|---|---|---|---|
| 1.1 | S | Impersonation via stolen refresh token | Device-bound refresh tokens; DPoP / mTLS for high-risk actions; refresh token rotation with reuse detection | `products/cymed/patient_portal/auth/` (tokens); mobile-app JWKS + attestation client code |
| 1.2 | T | On-device tampering / app repackaging | Play Integrity / DeviceCheck attestation on sensitive endpoints; jailbreak/root heuristics | attestation check middleware in `products/cymed/patient_portal/security/attestation.py` |
| 1.3 | R | Patient denies action (e.g., consent) | Cryptographically signed consent artefacts + append-only audit log; server-side event with device attestation | `products/cymed/patient_portal/consent/`; audit sink |
| 1.4 | I | PHI in URL / query strings | Enforce POST for PHI; deny query params matching PHI schemas; strip PHI from logs; TLS 1.2+ minimum | API gateway config; log-scrubber middleware |
| 1.5 | D | App-side abuse causing backend overload | Per-user + per-device rate limits; adaptive throttling; circuit breakers | gateway rate-limit config; `shared/ratelimit/` |
| 1.6 | E | Privilege escalation via role confusion | Scope claims validated per endpoint; deny by default; RBAC checked at controller + object level | scope-check decorators; RBAC middleware |

## 3. Patient portal (web) ↔ API gateway

| # | STRIDE | Threat | Mitigation | Code / config |
|---:|---|---|---|---|
| 2.1 | S | Phishing / session hijack | MFA (WebAuthn preferred, OTP fallback); short session TTL; step-up auth for sensitive actions | `products/cymed/patient_portal/auth/` |
| 2.2 | T | CSRF | SameSite=Strict cookies; anti-CSRF token on state-changing requests; Origin/Referer validation | Django CSRF middleware; `settings.py` |
| 2.3 | T | XSS injection into notes visible to patients | Output encoding by default; content sanitisation on stored HTML; strict CSP with nonces | template layer; CSP header config |
| 2.4 | R | Patient repudiates data-share consent | Signed, timestamped consent records; audit log linked to session + IP + user-agent hash | consent service; audit sink |
| 2.5 | I | Session cookies stolen via XSS | HttpOnly cookies; Secure flag; strict CSP; Trusted Types where supported | HTTP security middleware |
| 2.6 | D | Credential stuffing / bot login | Bot detection; per-account rate limits; exponential backoff; CAPTCHA on high-risk paths | login controller + WAF |
| 2.7 | E | IDOR — accessing another patient's data | Object-level access checks enforced in query layer; row-level security in DB | `products/cymed/*/access.py`; DB RLS policies |

## 4. Provider portal ↔ API gateway

| # | STRIDE | Threat | Mitigation | Code / config |
|---:|---|---|---|---|
| 3.1 | S | Credential theft of clinician account | Mandatory MFA; SSO with tenant IdP; short session; device posture check for privileged roles | tenant IdP config; auth middleware |
| 3.2 | T | Order tampering in transit | mTLS internal; write-once audit for orders; digital signature on signed orders | `products/cymed/hospital/orders/` |
| 3.3 | R | Clinician denies signing a note | Non-repudiable signature (server-side signed w/ user key + timestamp + hash of content); audit log entry with actor + reason | `products/cymed/hospital/documents/signing.py` |
| 3.4 | I | Snooping — accessing a chart without a care relationship | Break-glass workflow with reason + notification; access reviews; PHI query telemetry with anomaly detection | break-glass service; audit review job |
| 3.5 | D | Bulk export blocking clinical work | Rate limits on bulk endpoints; async job with quota; priority queues for clinical vs. reporting | bulk export controller |
| 3.6 | E | Role misconfiguration granting excess access | Least-privilege role templates; policy tests in CI; drift detection on role definitions | RBAC tests; policy-as-code |

## 5. Admin / control plane ↔ management API

| # | STRIDE | Threat | Mitigation | Code / config |
|---:|---|---|---|---|
| 4.1 | S | Compromise of a CyMed staff account | SSO with SAML/OIDC, WebAuthn MFA, hardware key requirement for prod; JIT elevation with approval | control-plane IdP + JIT service |
| 4.2 | T | Malicious change to a tenant | Two-person rule for destructive ops; signed change records; drift monitoring | control-plane service; approval workflow |
| 4.3 | R | Support engineer denies action | Every action carries a signed reason string; immutable audit log; monthly reviews | audit service |
| 4.4 | I | Cross-tenant leakage in support | Tenant scope enforced on every management operation; tests for tenant isolation | `shared/multitenant/`; isolation tests |
| 4.5 | D | Runaway migration jobs | Concurrency limits; kill-switch on tenant impact; canary tenants first | migration framework |
| 4.6 | E | Escalation from support to super-admin | Separation of duties: super-admin role gated by two-person approval; time-boxed | JIT service |

## 6. NPHIES bridge (external national exchange)

| # | STRIDE | Threat | Mitigation | Code / config |
|---:|---|---|---|---|
| 5.1 | S | Spoofed responses from a rogue peer | mTLS with pinned certs to NPHIES endpoints; response validation against schema and signatures | `products/cymed/nphies/client.py` |
| 5.2 | T | Payload tampering | Signature validation; canonicalised JSON hashing; TLS 1.2+ with strong ciphers | NPHIES adapter |
| 5.3 | R | Payer disputes what was submitted | Immutable submission log with request/response payload hashes; replayable evidence pack | NPHIES audit store |
| 5.4 | I | PHI overshared beyond minimum necessary | Field-level minimum-necessary filters per transaction type; validation before dispatch | request builder + tests |
| 5.5 | D | External outage cascades into ED | Circuit breaker; queue with backpressure; degraded mode with paper-fallback flag | resilience layer |
| 5.6 | E | Cross-tenant reuse of a payer credential | Per-tenant secrets in KMS with strict IAM; explicit tenant-in-request assertion | secrets store + policy |

## 7. Payment gateway integration

| # | STRIDE | Threat | Mitigation | Code / config |
|---:|---|---|---|---|
| 6.1 | S | Fake webhook posting fake payment | Signed webhook (HMAC) with rotating shared secret; source IP allowlist | webhook handler |
| 6.2 | T | Amount tampering between UI and gateway | Server-side price calculation; gateway session bound to server-computed total | checkout service |
| 6.3 | R | User denies a payment | Idempotent PSP references stored; receipt sent; audit event linked to session | payment service |
| 6.4 | I | Card data touching our systems | Tokenisation only; card data never traverses our servers; PCI DSS scope minimised | client-side gateway SDK |
| 6.5 | D | Payment API abuse | Per-user + per-IP throttling; anomaly detection; captcha on repeat failures | rate limiter |
| 6.6 | E | Refund from unauthorised role | Refund gated by role + amount thresholds + dual approval above threshold | payment service authz |

## 8. Image-share links (external)

| # | STRIDE | Threat | Mitigation | Code / config |
|---:|---|---|---|---|
| 7.1 | S | Link forwarded and re-used | Short TTL (default 24 h); optional one-time-use; optional passphrase; watermarking | `products/cymed/imaging/share_links.py` |
| 7.2 | T | URL parameter tampering | Signed opaque token; server-side authorisation on redemption | share-link service |
| 7.3 | R | Patient denies sharing | Consent capture with device + timestamp; audit event | share-link service |
| 7.4 | I | PHI in link metadata | Opaque token; no PHI in URL; response strips derivable identifiers | share-link service |
| 7.5 | D | Bulk enumeration of share links | Sufficient token entropy (≥ 128 bits); per-IP throttling; alerting on high-rate 404s | rate limiter + WAF |
| 7.6 | E | Link grants more than intended (e.g., full patient chart) | Scope of share limited to specific `ImagingStudy` and specified series; explicit allow-list | share-link service |

## 9. DICOM ingress (modalities, referring PACS)

| # | STRIDE | Threat | Mitigation | Code / config |
|---:|---|---|---|---|
| 8.1 | S | Rogue AE title impersonating a modality | Per-AE authentication with strong shared secrets or mTLS (DICOM-TLS); AE allowlist | `products/cymed/imaging/dicom_ingress/` |
| 8.2 | T | Study metadata alteration | Store received DICOM verbatim + hash; validate against `StudyInstanceUID`; refuse mismatches | ingress verifier |
| 8.3 | R | Modality disputes a study transfer | C-STORE receipt logs with hashes; C-FIND / C-MOVE audit; TLS handshake logs | DICOM audit store |
| 8.4 | I | Sensitive images exposed to wrong tenant | Tenant assertion required per AE; patient MRN resolved against tenant MPI; rejects on ambiguity | ingress classifier |
| 8.5 | D | Flood of instances from a modality | Per-AE rate + concurrency limits; disk quota; overflow to quarantine bucket | ingress guard |
| 8.6 | E | Ingress running with excessive DB privileges | Ingress service uses a scoped DB role limited to imaging tables + audit | DB roles + service policy |

## 10. Cross-cutting mitigations

| # | Control | Where |
|---:|---|---|
| X.1 | Encryption in transit (TLS 1.2+ / mTLS internal) | ingress + service mesh config |
| X.2 | Encryption at rest (AES-256, envelope w/ KMS; per-tenant keys for larger editions) | storage layer |
| X.3 | Structured audit log (append-only, tamper-evident) | audit service `shared/audit/` |
| X.4 | Central secrets management (vault + rotation) | `shared/secrets/` |
| X.5 | SAST + SCA + secrets scanning in CI | `.github/workflows/security.yml` (or equivalent) |
| X.6 | Third-party pen test annually + regression per major release | see `docs/security/PENTEST_PACK.md` |
| X.7 | Backup + PITR + DR test | ops runbooks |
| X.8 | Incident response with 24/7 on-call | IR plan |

## 11. Residual risks and open items

- Mobile device attestation coverage limited on older Android versions — accepted with compensating detections.
- NPHIES sandbox regressions during regulator updates — mitigated by feature flag and payer fallback.
- Long-lived DICOM connections behind hospital firewalls — mitigated by health-checks and re-establishment logic.
- Third-party AI model providers (if enabled per tenant) — see DPA sub-processor table; opt-in only.

## 12. Review cadence and change log

- Reviewed each release for scope changes; each new integration adds a new boundary.
- Every SEV1 / SEV2 security incident triggers a review of the affected boundary.
