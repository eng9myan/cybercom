# P0-1 · Patient App + NFC Identity — Technical Spec

**Owner:** CyMed Platform · **Status:** SPEC · **Target:** Q1 Sprint 1-2
**Depends on:** existing `products.cymed.patient_portal`, `platform.common`, `platform.terminology`
**Blocks:** P0-2 Payments (needs auth), all portal features

---

## 1. Product Requirements

### Goals
- Single super-app for patient across hospital / clinic / pharmacy / lab / imaging in CyMed network.
- NFC card = physical identity. Tap at any provider reception → provider gets scoped access to patient record.
- Paramedic tap on NFC card in emergency → gets Emergency Profile (allergies, meds, conditions, next of kin) w/o full login.
- Family / delegated access: parent manages child, adult child manages elderly parent.
- Runs on iOS + Android (native) + Web PWA — one API, three shells.

### Non-Goals
- Not building payment gateway integrations here (P0-2).
- Not building NPHIES/JoFotara integrations here (P0-3, already scaffolded).

### Success Metrics
- < 2 s tap-to-access NFC latency.
- 99.5% NFC scan success rate.
- Patient can complete registration → view records → book appt in < 3 minutes.
- Emergency scan works offline (last-cached emergency profile on card issuer's device).

---

## 2. Auth Architecture

### Roles
| Role | Auth method | Access |
|---|---|---|
| Patient (own) | OAuth2 password / SMS OTP + biometric | full own record |
| Delegated payer (family) | OAuth2 + `delegation_scope` claim | scoped (see §5) |
| Provider (via NFC tap) | mTLS + one-time NFC token | scoped to encounter |
| Paramedic (emergency NFC) | mTLS + emergency scope | emergency profile only |

### Token flow
```
Patient login → POST /api/v1/patient-app/auth/login
  { username, password }  OR  { phone, otp }
→ 200 { access_token, refresh_token, biometric_challenge }

Biometric on device → device signs challenge with device-bound keypair (WebAuthn / SecureEnclave)
→ POST /api/v1/patient-app/auth/biometric  { assertion }
→ 200 { session_token }        # long-lived, revocable per device

NFC tap at provider terminal:
  Terminal reads NFC card → gets patient_uuid + card_signature
→ POST /api/v1/nfc/scan
    Authorization: Bearer <provider_terminal_token>
    { card_uuid, signature, purpose: 'reception'|'emergency'|'pharmacy'|... }
→ 200 { patient_summary, scoped_access_token }
    - purpose=reception: full record for encounter
    - purpose=emergency: emergency profile only (no login required beyond terminal)
```

### Threat model
- NFC card cloned → card_signature is per-card ECDSA key stored in secure element; revocable via `/nfc/revoke`.
- Terminal compromise → terminal tokens are short-lived (15 min) + tied to provider IP.
- Emergency abuse → every emergency scan logged, patient notified via push.

---

## 3. Data Model — additions to `patient_portal`

New models in `products/cymed/patient_portal/models.py`:

```python
class PatientDevice(BaseModel):
    """Registered mobile device for a patient (iOS/Android/Web)."""
    profile              = FK(PatientPortalProfile, related_name='devices')
    platform             = Choice('ios', 'android', 'web')
    device_id            = CharField(255, db_index=True)          # opaque, generated on install
    push_token           = CharField(500, blank=True)             # APNs/FCM/Web Push
    webauthn_credential  = TextField(blank=True)                  # base64 CBOR blob
    device_name          = CharField(200, blank=True)             # user-friendly
    last_seen_at         = DateTimeField(null=True)
    revoked              = Boolean(default=False)

class NFCCard(BaseModel):
    """Physical NFC card issued to a patient (or dependent)."""
    profile              = FK(PatientPortalProfile, related_name='nfc_cards')
    card_uuid            = UUIDField(unique=True, db_index=True)  # embedded on card
    public_key_pem       = TextField()                            # for signature verify
    issued_at            = DateTimeField(auto_now_add=True)
    issued_by            = FK('auth.User', null=True)             # issuing staff
    activated_at         = DateTimeField(null=True)
    revoked_at           = DateTimeField(null=True)
    revocation_reason    = CharField(200, blank=True)

class NFCScanLog(BaseModel):
    """Every tap logged for audit + patient visibility."""
    card                 = FK(NFCCard)
    scanned_at           = DateTimeField(auto_now_add=True, db_index=True)
    purpose              = Choice('reception','pharmacy','lab','imaging','emergency','other')
    provider_tenant_id   = UUIDField()                             # who scanned
    terminal_id          = CharField(200)                          # which terminal
    scope_granted        = JSONField()                             # what fields released
    patient_notified_at  = DateTimeField(null=True)

class EmergencyProfile(BaseModel):
    """Pre-computed emergency snapshot pushed to NFC-issuer device for offline paramedic scan."""
    profile              = OneToOne(PatientPortalProfile, related_name='emergency_profile')
    blood_type           = CharField(5)
    allergies            = JSONField(default=list)                 # [{substance, severity, reaction}]
    current_medications  = JSONField(default=list)                 # [{drug, dose, frequency}]
    chronic_conditions   = JSONField(default=list)                 # [{icd11, label}]
    emergency_contacts   = JSONField(default=list)                 # [{name, relation, phone}]
    dnr_status           = Choice('none','dnr','dnr_cc','unknown', default='unknown')
    organ_donor          = Boolean(default=False)
    religious_preferences= CharField(200, blank=True)
    preferred_language   = CharField(10, default='ar')
    updated_from_ehr_at  = DateTimeField(null=True)

class DelegatedAccess(BaseModel):
    """Family / caregiver access to another patient's records + wallet."""
    subject_profile      = FK(PatientPortalProfile, related_name='delegates_granted')
    delegate_profile     = FK(PatientPortalProfile, related_name='delegated_to_me')
    relationship         = Choice('spouse','parent','child','sibling','guardian','friend','other')
    scope_read_records   = Boolean(default=False)
    scope_book_appt      = Boolean(default=False)
    scope_pay_bills      = Boolean(default=True)
    scope_max_amount     = DecimalField(15, 2, null=True)          # cap per delegation
    scope_expiry         = DateTimeField(null=True)
    consent_signed_at    = DateTimeField()                         # subject's consent
    revoked_at           = DateTimeField(null=True)

class ConsentGrant(BaseModel):
    """Fine-grained data-sharing consent per provider."""
    profile              = FK(PatientPortalProfile, related_name='consents')
    provider_tenant_id   = UUIDField()
    scope                = JSONField()   # {resource: 'Observation', category: 'laboratory'} etc.
    purpose              = Choice('treatment','payment','operations','research')
    valid_from           = DateTimeField()
    valid_until          = DateTimeField(null=True)
    revoked_at           = DateTimeField(null=True)
```

Migrations: `python manage.py makemigrations patient_portal`.

---

## 4. OpenAPI 3.1 Endpoints (Patient App API)

Base: `/api/v1/patient-app/`

### Auth
```
POST   /auth/register              { phone, national_id, dob } → OTP sent
POST   /auth/verify-otp            { phone, otp } → { access_token, needs_biometric }
POST   /auth/login                 { username, password }
POST   /auth/biometric/challenge   → { challenge }
POST   /auth/biometric/verify      { assertion } → { session_token }
POST   /auth/refresh               { refresh_token } → { access_token }
POST   /auth/logout                → 204
GET    /auth/devices               → [PatientDevice]
DELETE /auth/devices/{id}          → 204
```

### Profile & Emergency
```
GET    /profile/me                 → PatientPortalProfile+
PATCH  /profile/me                 { language, theme, preferences }
GET    /profile/emergency          → EmergencyProfile   (patient view)
PATCH  /profile/emergency          { allergies, meds, contacts, dnr_status }
```

### NFC
```
GET    /nfc/cards                  → [NFCCard]  (my cards)
POST   /nfc/cards                  → { card_uuid, activation_code }  (staff issues)
POST   /nfc/cards/{id}/activate    { activation_code, device_public_key }
POST   /nfc/cards/{id}/revoke      { reason }
GET    /nfc/scans                  → [NFCScanLog]  (my scan history)
```

### NFC public (called by provider terminal)
```
POST   /nfc/scan
  Auth: Bearer <terminal_token>
  Body: { card_uuid, signature, purpose, terminal_id }
  → 200: { patient_summary, scoped_access_token, expires_in }
       patient_summary depends on purpose:
         - reception     : {name, mrn, dob, phone, insurance, allergies}
         - emergency     : full EmergencyProfile
         - pharmacy      : {name, mrn, allergies, active_rx}
         - lab / imaging : {name, mrn, dob, referring_dr}
```

### Records aggregation (across ecosystem)
```
GET    /records/timeline           → paginated [encounters, obs, results, rx, imaging]
GET    /records/appointments       → upcoming + past
POST   /records/appointments       { provider_id, service_id, slot } → booking
DELETE /records/appointments/{id}  → cancellation
GET    /records/labs               → [DiagnosticReport]  (FHIR-shaped)
GET    /records/labs/{id}          → full report + trend
GET    /records/imaging            → [ImagingStudy]
GET    /records/imaging/{id}/viewer→ signed URL to DICOM viewer
GET    /records/prescriptions      → [MedicationRequest]
POST   /records/prescriptions/{id}/refill  → routed to pharmacy of choice
GET    /records/documents          → [DocumentReference]
GET    /records/documents/{id}     → signed PDF URL
```

### Delegated access
```
GET    /delegations/granted        → [DelegatedAccess]  (I gave)
GET    /delegations/received       → [DelegatedAccess]  (I got)
POST   /delegations                { subject_id, scope, expiry } → invite sent
POST   /delegations/{id}/accept    → 200
POST   /delegations/{id}/revoke    → 204
GET    /delegations/{id}/records   → subject's records (respects scope)
```

### Consent
```
GET    /consents                   → [ConsentGrant]
POST   /consents                   { provider, scope, purpose, expiry }
DELETE /consents/{id}              → revoke
```

### Payments / Insurance (thin wrappers → P0-2 handles internals)
```
GET    /billing/bills              → [UnifiedBill]  (own + delegated subjects)
GET    /billing/bills/{id}         → detailed w/ insurance split
POST   /billing/bills/{id}/pay     { method, source_wallet, on_behalf_of }
GET    /billing/insurance          → [InsurancePolicy]
POST   /billing/insurance          { insurer, policy_number, member_no } → verified
POST   /billing/insurance/{id}/eligibility { service_code } → coverage response
POST   /billing/insurance/{id}/preauth     { service_code, provider } → status
```

### Wearables / RPM (stub for later)
```
POST   /wearables/connect          { vendor: apple_health|fitbit|garmin }
POST   /wearables/observations     [{ code, value, unit, timestamp }]
```

### Notifications
```
POST   /notifications/register-push { device_id, push_token }
GET    /notifications              → [Notification]
PATCH  /notifications/{id}         { read: true }
```

Full OpenAPI YAML lives at `docs/specs/openapi/patient_app.yaml` (generated next commit).

---

## 5. NFC Scan Flow — sequence

### Reception scan (routine)
```
1. Patient hands NFC card to reception clerk.
2. Reception terminal (kiosk / staff tablet) reads NFC → gets card_uuid + signs a nonce w/ card key.
3. Terminal POST /nfc/scan { card_uuid, signature, purpose: 'reception', terminal_id }.
4. Server:
   a. Verifies signature against NFCCard.public_key_pem.
   b. Checks card not revoked, patient not blocked.
   c. Creates NFCScanLog (audit).
   d. Issues scoped_access_token bound to terminal_id + encounter (valid 4h).
   e. Sends push notification to patient: "Riyadh Hospital reception accessed your card at 11:42."
5. Reception UI now has patient_summary; scans supplies etc using scoped_access_token.
```

### Emergency scan (paramedic)
```
1. Paramedic device (issued by regional health authority) has emergency-capable client.
2. Taps unconscious patient's NFC card.
3. Client extracts card_uuid → tries POST /nfc/scan { purpose: 'emergency' }.
4. If online → server returns EmergencyProfile + logs.
5. If offline (rural) → device has last-cached EmergencyProfile signed by CyMed root; validates signature and shows offline copy.
6. When online → device syncs the offline scan event to server for audit.
7. Patient (or emergency contacts) receive push: "Emergency scan of your card by Riyadh Paramedic Unit 12 at 14:22."
```

### Provider terminal registration (one-time)
```
Admin registers terminal in provider dashboard → gets terminal_id + long-lived terminal_secret (mTLS cert).
Terminal exchanges cert for short-lived terminal_token via /api/v1/nfc/terminal/token every 15 min.
```

---

## 6. Mobile App Architecture — Flutter

### Why Flutter (over React Native)
- Single codebase → iOS + Android + Web PWA.
- Better NFC package maturity (`nfc_manager`) on both platforms.
- Team already used to Dart for CyID mobile wallet.

### Package layout
```
mobile/patient_app/
├── lib/
│   ├── main.dart
│   ├── app.dart                    # MaterialApp + router
│   ├── theme/
│   │   ├── colors.dart             # CyMed brand
│   │   ├── glassmorphism.dart      # design system
│   │   └── dark_mode.dart
│   ├── router.dart                 # go_router
│   ├── auth/
│   │   ├── auth_repo.dart
│   │   ├── biometric_service.dart  # local_auth
│   │   └── screens/
│   ├── nfc/
│   │   ├── nfc_service.dart        # nfc_manager
│   │   ├── card_activation.dart
│   │   └── emergency_reader.dart
│   ├── records/
│   │   ├── timeline.dart
│   │   ├── lab_result_detail.dart
│   │   ├── imaging_viewer.dart     # OHIF web viewer in WebView
│   │   └── prescription_refill.dart
│   ├── appointments/
│   ├── payments/                   # thin wrappers → P0-2
│   ├── delegated/                  # family accounts
│   ├── consent/
│   ├── wearables/
│   └── api/
│       ├── client.dart             # dio + interceptors
│       └── generated/              # openapi_generator
├── ios/                            # Xcode project
├── android/                        # Gradle project
└── pubspec.yaml
```

### Key deps
```yaml
dependencies:
  flutter:
  go_router: ^15                    # navigation
  dio: ^5                           # HTTP
  flutter_secure_storage: ^10       # tokens
  local_auth: ^2                    # biometric
  nfc_manager: ^4                   # NFC read/write
  webview_flutter: ^5               # OHIF DICOM viewer, Zakat/Jofotara PDFs
  fl_chart: ^1                      # lab trends
  intl: ^0.20                       # Hijri + i18n
  hive_flutter: ^2                  # offline cache
  firebase_messaging: ^16           # push
  package_info_plus: ^9
```

### Screens (deep-link + tab structure)
```
/onboarding      Splash → Language → Login → Biometric setup
/home            Dashboard: next appt, active meds, unread results, wallet balance
/records         Timeline tab · Labs tab · Imaging tab · Rx tab · Documents tab
/appointments    Upcoming list + book flow (provider directory search → slot picker → confirm)
/nfc             My cards · Recent scans · Emergency profile
/family          Delegated accounts list + invite flow
/payments        Bills + Insurance cards + Delegated payments (→ P0-2 shells)
/settings        Profile · Consent · Notifications · Devices · Language
```

### PWA build
Same Flutter codebase — `flutter build web --release --pwa-strategy offline-first`. Serve from Django at `/patient-app/` behind auth.

---

## 7. i18n / RTL

- Default locale = `ar_SA`. Fallback = `en`.
- `flutter_localizations` + custom Arabic medical terminology dictionary at `assets/i18n/ar_medical.json`.
- Hijri calendar picker via `hijri` package for date-of-birth + appointment slots.
- All text right-aligned in ar; icons mirrored where directional (arrows, back button).

---

## 8. Security & Compliance hooks

| Concern | Control |
|---|---|
| Token storage | `flutter_secure_storage` → Keychain (iOS) / EncryptedSharedPreferences (Android) |
| Biometric bind | Device generates ECDSA keypair in Secure Enclave / StrongBox on registration |
| Screenshots | Block on Rx/lab detail screens (`SystemChrome.setEnabledSystemUIMode` + FLAG_SECURE) |
| Root/jailbreak detect | `flutter_jailbreak_detection` — block auth if detected |
| Cert pinning | `dio_http2_adapter` + pinned SPKI for `api.cymed.sa` |
| Audit | Every NFC scan + delegated access logged in `PatientPortalActivity` and mirrored to `platform.audit` |
| Data at rest | Hive box encryption key stored in secure storage |
| HIPAA/GxP | Server-side row-level tenant filter never bypassed; delegated_by user_id always recorded |

---

## 9. Rollout plan

**Sprint 1 (weeks 1-2)** — server:
- Models + migrations for PatientDevice / NFCCard / NFCScanLog / EmergencyProfile / DelegatedAccess / ConsentGrant.
- Auth endpoints (register, otp, login, biometric challenge/verify).
- NFC endpoints (issue, activate, revoke, scan, terminal token).

**Sprint 2 (weeks 3-4)** — server:
- Records aggregation endpoints (timeline, labs, imaging, prescriptions).
- Delegated access + consent endpoints.
- OpenAPI generated + published to `/api/docs`.

**Sprint 3 (weeks 5-6)** — Flutter:
- Project scaffold + design system + auth flow + biometric.
- Home dashboard + records timeline + appointment booking.

**Sprint 4 (weeks 7-8)** — Flutter:
- NFC screens (my cards, scans, emergency profile edit).
- Delegated family screens.
- PWA build + Django wiring.

**Sprint 5 (week 9)** — QA + pilot:
- Pen-test.
- Play Store / App Store submissions.
- Pilot with 1 hospital reception + 5 patients.

---

## 10. Open decisions (need input before code sprint)

1. **NFC chip vendor** — NXP MIFARE DESFire EV3 (recommended: crypto in chip) vs. NTAG424 DNA (cheaper).
2. **APNs/FCM cost centre** — under which tenant? Suggest platform-level with per-tenant billing.
3. **Emergency scan offline cache expiry** — 24h vs 72h. Longer = more useful, less secure.
4. **Consent granularity** — per-encounter (annoying but safest) vs per-provider blanket (simpler).

Recommend defaults: DESFire EV3, platform-billed, 48h offline cache, per-provider consent w/ resource-type filters.

---

## 11. Next artifact

`docs/specs/openapi/patient_app.yaml` — full OpenAPI 3.1 spec for §4 endpoints, generated in next commit.

Then P0-1 CODE task begins: models + migrations + auth + NFC endpoints in Django, followed by Flutter scaffold.
