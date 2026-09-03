# GDPR Compliance Checklist — CyMed

## Data controller / processor
- **Controller:** the healthcare provider (hospital / clinic / pharmacy / lab / imaging tenant).
- **Processor:** CyMed Healthcare Systems.
- **Sub-processors:** payment gateways, insurer clearinghouses, cloud host — enumerated in DPA appendix.

## Articles map

| Article | Status | Evidence |
|---|---|---|
| Art 5 — lawful/fair/transparent | ⚠ | Privacy notice draft in mobile app; align with Arabic + English versions |
| Art 6 — lawfulness of processing | ✅ | Explicit consent capture in `patient_portal.PatientPortalProfile.data_sharing_consent` |
| Art 7 — conditions for consent | ✅ | Timestamp + IP + user_agent on `consentTreatmentAt` |
| Art 9 — special-category (health) | ✅ | Explicit consent + healthcare-provision legal basis; audit trail |
| Art 12-14 — information to subject | ⚠ | Onboarding screen in Flutter; ensure Arabic RTL parity |
| Art 15 — right of access | ✅ | `/api/v1/patient-app/records/timeline` returns full timeline export |
| Art 16 — right to rectification | ✅ | `/profile/me` PATCH endpoint |
| Art 17 — right to erasure | ⚠ | Soft-delete implemented; hard erasure workflow needs wizard |
| Art 18 — restriction of processing | ⚠ | Consent revocation partially in place; needs "pause" state |
| Art 20 — data portability | ✅ | FHIR R4 REST server exposes full record in FHIR JSON |
| Art 21 — right to object | ⚠ | UI toggle in Flutter settings |
| Art 25 — privacy by design | ✅ | Multi-tenant RLS + per-field encryption + minimum necessary |
| Art 30 — records of processing | ⚠ | ROPA spreadsheet under legal review |
| Art 32 — security of processing | ✅ | See HIPAA_CHECKLIST §164.312 |
| Art 33 — breach notification (72h) | ⚠ | See `INCIDENT_RESPONSE_PLAN.md` |
| Art 35 — DPIA | ⚠ | DPIA template `DPIA_TEMPLATE.md` (to write) — required for new sub-processors |
| Art 44-49 — international transfers | ⚠ | Cloud region defaults to local (SA/JO/EU); SCCs for cross-border |

## Data subject request workflow

Automated endpoints for the 3 most common DSRs:
- **Access** — `GET /api/v1/patient-app/records/timeline?format=fhir-bundle`
- **Portability** — `GET /fhir/R4/Patient/{id}?$everything`
- **Erasure** — `POST /api/v1/patient-app/gdpr/erasure-request` (staff review 30-day SLA)

## Next actions

1. Publish Arabic + English privacy notice (legal review).
2. Build hard-erasure wizard: cascade-delete PHI across all modules with audit copy.
3. Sign SCCs with all sub-processors.
4. Add "download my data" button in Flutter settings.
