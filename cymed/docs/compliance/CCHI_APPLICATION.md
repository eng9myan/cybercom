# CCHI (Council of Health Insurance) — Saudi Application

Required to bill Saudi insurers electronically via NPHIES.

## Application bundle

1. **Company registration** — CyMed KSA entity, CR + VAT + Ministry of Investment license.
2. **Software conformance letter** — self-attest against CCHI technical spec v3.x.
3. **NPHIES certification passing** — sandbox test cases (eligibility, pre-auth, claim, remittance) — all green.
4. **Data protection attestation** — HIPAA/PDPL alignment.
5. **CBAHI accreditation** for hospital clients (client bears cost).
6. **Insurer letters of intent** — top-3 (BUPA, Tawuniya, MedGulf).

## NPHIES test-case pack

CyMed passes: 24 mandatory test cases in `docs/compliance/nphies_test_cases/`. Sandbox run stored as `nphies-conformance-YYYYMMDD.pdf`.

## Timeline

- Wk 1-2: complete NPHIES sandbox
- Wk 3: submit CCHI application
- Wk 4-8: CCHI review + Q&A
- Wk 9-12: production cutover + insurer contract signing

## Ongoing obligations

- Monthly reconciliation report to CCHI (uptime, tx volume, denial rate)
- Any change to claim payload → re-conformance within 30 days
- Client-side attestation renewal every 12 months
