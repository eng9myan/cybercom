# CyED — Hardware & Provider Integration Guide

CyED is **software-complete and hardware-ready**: every device/provider feature is
built up to a single, documented seam. Plug in the hardware or provider and it
works — no CyED code changes, no stubs to replace in the domain logic.

Each seam is **env-gated** and **fail-safe**: when the provider is off, CyED still
works (stores the data, returns `pending`, uses a deterministic fallback), and any
device that already produces the output (text, transcript, GPS fix) can POST it
directly to the same endpoints.

## 1. Bus GPS tracking + ETA
- **Device posts:** `POST /api/v1/transport/locations/` `{bus, lat, lng, speed_kmh, heading}` (staff/service credential).
- **Parents read:** `GET /api/v1/transport/buses/<bus_id>/live/` → latest position + per-stop ETA (scoped to their child's bus).
- **Route optimization:** `POST /api/v1/transport/routes/<id>/optimize/` (real greedy nearest-neighbour; a traffic-aware provider slots behind `transport/routing.py:optimize_order`).
- **Hardware:** any GPS tracker that can HTTP POST. Live map UI: `/bus-tracking`.

## 2. RFID / tap on-off bus
- **Reader posts:** `POST /api/v1/transport/boarding-events/` `{student, bus, event_type}`.
- **Effect:** signal auto-notifies guardians ("child safely boarded Bus #12").
- **Hardware:** RFID/NFC reader or scanning wristband → POST per tap.

## 3. Facial-recognition attendance kiosk
- **Seam:** the kiosk performs matching **on-device** (privacy — raw images never leave the kiosk; store only the vector, per ST4S) and posts the resolved student.
- **Kiosk posts:** create attendance marks via `POST /api/v1/attendance/marks/` (or roll calls). The education logic (roll call, parent absence alerts) is already built.

## 4. OCR document intake
- **Seam:** `intake/ocr.py:extract_text` (env `CYED_OCR_ENABLED`; provider = Tesseract / AWS Textract / Azure Doc Intelligence).
- **Endpoints:** `POST /api/v1/intake/documents/` (multipart `file`, or JSON `raw_text` if the device already OCR'd) → **real field extraction** (name/DOB/number) runs regardless.
- **Reprocess:** `POST /api/v1/intake/documents/<id>/reprocess/` with `raw_text`.

## 5. AI meeting scribe (speech-to-text)
- **Seam:** `meetings/stt.py:transcribe` (env `CYED_STT_ENABLED`; provider = Whisper / AWS Transcribe / Azure Speech).
- **Endpoints:** `POST /api/v1/meetings/sessions/` (`audio` file, or `transcript` directly) → **real summariser** extracts summary + action items + key points regardless of provider.

## 6. LLM (Anthropic) for the education AI
- **Seam:** `ai_agents/llm.py` (env `CYED_LLM_ENABLED` + `CYED_ANTHROPIC_API_KEY`). Off → deterministic grounded fallback. All agents (tutor, Socratic, teacher tools, scribe) use this one seam.

## 7. Notifications (SMS / WhatsApp / push)
- **Seam:** `notifications/delivery.py` — in-app delivered now; external channels queue until `CYED_NOTIFY_<CHANNEL>_ENABLED` (Twilio / WhatsApp Business / FCM).

## 8. Payments gateway
- **Seam:** billing records payments + statuses; a gateway (Stripe / BPAY / Ezidebit) posts confirmed payments to `POST /api/v1/billing/installments/<id>/pay/`.

## Device authentication (recommended)
Devices/readers should authenticate with a **service account** in CyIdentity
holding a staff/service role (they hit staff-only POST endpoints). mTLS + per-device
client certs at the API gateway (Kong/NGINX) is the recommended transport hardening
(matches the ST4S checklist). No device credential is embedded in CyED itself.

## Environment flags summary
| Flag | Enables |
|---|---|
| `CYED_LLM_ENABLED` + `CYED_ANTHROPIC_API_KEY` | Live LLM for all AI agents |
| `CYED_OCR_ENABLED` | OCR provider for document intake |
| `CYED_STT_ENABLED` | Speech-to-text for the meeting scribe |
| `CYED_NOTIFY_SMS_ENABLED` / `_WHATSAPP_ENABLED` / `_PUSH_ENABLED` | External notification channels |
| `CYED_CYCOM_URL` | Generic ERP reuse from CyCom (`/api/v1/erp/...`) |
