# CyMed Patient App (Flutter)

iOS + Android + Web PWA from single Dart codebase.

## Prerequisites
- Flutter SDK 3.24+
- Xcode 15 (iOS) or Android Studio + JDK 17
- Firebase project for push (optional in dev)

## Setup
```bash
cd mobile/patient_app
flutter pub get
```

## Run

### iOS
```bash
open ios/Runner.xcworkspace         # first time — configure signing
flutter run -d iphone
```

### Android
```bash
flutter run -d android
```

### Web (PWA)
```bash
flutter build web --release --pwa-strategy=offline-first
# Build output → build/web
cp -r build/web/* ../../static/patient_app/    # served by Django at /patient-app/
```

## Environment
Pass API base URL at build time:
```bash
flutter run --dart-define=CYMED_API_URL=https://api.cymed.sa/api/v1/patient-app
```

Defaults to `https://sandbox.cymed.sa/api/v1/patient-app` if omitted.

## Package layout
```
lib/
  main.dart                app entrypoint
  app.dart                 MaterialApp + theme
  router.dart              go_router
  theme/                   CyMed brand colors
  auth/                    login, OTP, biometric setup
  records/                 timeline, labs, imaging, prescriptions
  appointments/            book/list
  nfc/                     card, emergency profile
  delegated/               family
  payments/                bills, insurance (thin shells → P0-2)
  consent/                 grants
  api/                     dio client + secure storage
```

## Security
- Tokens in `flutter_secure_storage` (Keychain / EncryptedSharedPreferences).
- Biometric via `local_auth` — WebAuthn keypair bound to device.
- Screenshot block via `FLAG_SECURE` on Rx / lab / imaging screens.
- Jailbreak / root detection via `flutter_jailbreak_detection`.

## Build .ipa / .aab
```bash
flutter build ios --release            # → build/ios/iphoneos/Runner.app (archive in Xcode)
flutter build appbundle --release      # → build/app/outputs/bundle/release/app-release.aab
```
