# CyMed Patient Integration in the Super App — Status

Status: blocked on a real architectural gap, documented rather than
worked around. Part of Phase 4.

## What's blocking patient self-service screens

Checked `cymed/products/cymed/core/patients/models.py` — the `Patient`
model has **no link to a CyIdentity user account** (no `keycloak_user_id`
or equivalent field). Patient records are created and managed by clinical
staff (registration desk), not tied 1:1 to a login.

This is exactly what the `patient_portal` product was for in the original
CyberCom-Platform source — it owned that Patient-to-CyIdentity linkage
plus patient-scoped serializers/permissions (a patient can only ever see
their own encounters/labs/imaging/prescriptions, never another patient's).
`patient_portal` was explicitly excluded from the `cymed/` import (Phase 0
scope decision — hospital, clinic, laboratory, pharmacy, imaging only).

Building "patient views their own medical records" screens against the
current `cymed/` backend without that linkage would mean either:
- Inventing a Patient-CyIdentity link field now, un-reviewed, in a
  healthcare data model — the kind of unauthorized scope change rule #20
  says to stop and document instead of doing silently.
- Building screens that query patient data by patient_id without a real
  per-patient access check, which would be a genuine authorization bug
  (a patient could view another patient's records) — not shipping that.

## What's real and buildable without patient_portal

CyMed's `core` app (already in scope) has `providers`, `facilities`, and
`scheduling` — enough for **staff-facing** mobile tools: look up a
patient (with real staff-role authorization), book an appointment,
review a patient's encounters/lab/imaging/pharmacy records as an
authorized clinician. This is a different but legitimate reading of
master spec section 14 — provider-side mobile access, not patient
self-service.

## Recommendation

Re-scope this explicitly with a product decision before building either
direction:
1. Import `patient_portal` now (expands the original Phase 0 import
   decision) and build real patient self-service screens against it, or
2. Build staff/clinician-facing CyMed mobile screens against what's
   already in scope, and treat true patient self-service as a later,
   separately-scoped phase.

Not building either blind. Flagging for a decision rather than guessing.
