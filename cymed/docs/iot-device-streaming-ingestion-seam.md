# IoT / Device Streaming Ingestion Seam (Design Only)

**CyID ecosystem, Phase 10.** This is a design document, not an implementation — per the CyID ecosystem plan, real-time device integration (ICU vitals monitors, IV pumps, bedside telemetry) is deliberately deferred: there is no hardware or vendor simulator available in this environment to build and verify working code against, and unverifiable "integration" code is worse than no code. What follows is the contract a future device-integration phase should implement against, so that work can start without redesigning the seam.

## Where this anchors in the existing schema

`cymed/products/cymed/core/orders/models.py` already has the exact seam this needs:

```python
class OrderResult(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="results")
    result_text = models.TextField()
    result_reference_id = models.UUIDField(null=True, blank=True)  # maps to Observation or diagnostic report
    recorded_at = models.DateTimeField(default=timezone.now)
    recorded_by = models.CharField(max_length=255)
```

`result_reference_id` was added with the comment "maps to Observation or diagnostic report" but nothing has ever written a real Observation there — it's an intentional, unimplemented seam, not dead code. The design below is what should populate it.

Separately, `core/clinical/models.py`'s `Observation` model (LOINC code, `value_quantity`/`value_string`, status preliminary/final/amended) is already FHIR-Observation-shaped at the field level (confirmed this session, see the CyID ecosystem plan's research notes) — a device-streaming Observation should be a real row in *that* table, with `OrderResult.result_reference_id` pointing at its `id`. No new "Observation" model needs to be invented; the real gap is the ingestion path that creates rows there from a device feed, plus somewhere to hold the raw high-frequency samples underneath a periodic clinical Observation.

## Ingestion contract

### Payload shape (FHIR R4 Observation, trimmed to what device gateways would actually send)

```json
{
  "resourceType": "Observation",
  "status": "preliminary",
  "code": { "coding": [{ "system": "http://loinc.org", "code": "8867-4", "display": "Heart rate" }] },
  "subject": { "reference": "Patient/<patient_id>" },
  "encounter": { "reference": "Encounter/<encounter_id>" },
  "device": { "identifier": { "system": "urn:cymed:device", "value": "<device_id>" } },
  "effectiveDateTime": "2026-07-21T10:15:32Z",
  "valueQuantity": { "value": 78, "unit": "beats/minute", "system": "http://unitsofmeasure.org", "code": "/min" },
  "component": [
    { "code": { "coding": [{ "system": "http://loinc.org", "code": "8480-6", "display": "Systolic BP" }] }, "valueQuantity": { "value": 118, "unit": "mmHg" } },
    { "code": { "coding": [{ "system": "http://loinc.org", "code": "8462-4", "display": "Diastolic BP" }] }, "valueQuantity": { "value": 76, "unit": "mmHg" } }
  ]
}
```

This is a standard FHIR Observation with `component` used for multi-value readings (BP systolic/diastolic in one sample), matching how real bedside monitors group readings.

### Endpoint shape

`POST /api/v1/core/device-observations/` (new, not yet built):
- Auth: a `ServicePrincipal` (already a real model in `platform/cyidentity/models.py`, M2M workload identity — exactly what a device gateway is) rather than a clinician's own token.
- Body: the Observation JSON above, one per sample or a small batch.
- Behavior: validates `subject`/`encounter` resolve to a real `Patient`/`Encounter` in the caller's tenant, writes a real `core.clinical.Observation` row, and — if the payload includes an `orderId` extension (linking the reading to a specific active `Order`, e.g. a continuous-monitoring order) — creates a matching `OrderResult` with `result_reference_id` set to the new Observation's id. This is the one line of real code the whole design is oriented around; everything else here is architecture around getting a validated payload to that point safely.
- Idempotency: device gateways retry on network failure — the endpoint should key on `(device_id, effectiveDateTime, code)` to reject exact duplicates, not just accept-and-append blindly.

## Data store choice: two tiers, not one

A single high-frequency vitals stream (e.g. a monitor sampling every second) does not belong in the same Postgres table as clinical Observations queried by clinicians — that's a write-volume and query-shape mismatch, not just a scale concern.

- **Clinical tier (Postgres, existing `core.clinical.Observation` table)** — periodic/significant readings only (e.g. one HR reading per minute, or on-threshold-breach), the ones a clinician actually reviews. This is what `OrderResult.result_reference_id` points at.
- **Raw telemetry tier (time-series store, new — not yet chosen or provisioned)** — the actual per-second/per-beat waveform data, if that granularity is ever needed (e.g. for retrospective arrhythmia analysis). Candidates: TimescaleDB (Postgres extension — lowest operational overhead, reuses the existing Postgres fleet and `psycopg` driver already in every product's requirements.txt) or InfluxDB (purpose-built, more tooling, one more service to run and secure). Recommendation when this is actually built: start with TimescaleDB specifically because it avoids introducing a second database technology into a stack that doesn't have one yet — revisit only if query patterns genuinely need InfluxDB's continuous-query/downsampling features TimescaleDB can't match.

A device gateway would write raw samples to the time-series tier directly (not through the Django API at all — too much per-sample overhead) and call the `/device-observations/` endpoint above only for the periodic/significant clinical-tier Observation, with a reference (e.g. a time-range query the clinical UI can use) back into the time-series tier for "show me the raw waveform around this reading."

## Coding-system validation

`platform/terminology/providers/fhir.py`'s `FHIRTerminologyProvider` already does real `$validate-code` calls against a configurable `FHIR_TERMINOLOGY_SERVER` (confirmed this session — terminology-only today, not clinical-resource FHIR, but a working precedent for calling a real FHIR endpoint). The device-observations endpoint should validate every incoming LOINC `code` against this provider before writing an Observation — reuse, not rebuild.

## What this design deliberately does not decide

- Which real device/vendor protocol (HL7v2, a specific monitor vendor's API, MQTT) a gateway process would speak upstream of this contract — that depends entirely on which physical hardware is procured, which hasn't happened.
- Alerting/threshold-breach logic (e.g. push a notification when HR exceeds a range) — a real feature, but layered on top of Observations existing at all, not part of the ingestion contract itself.
- Whether the time-series tier is multi-tenant-shared or per-tenant — needs real volume estimates from an actual device deployment to size correctly, which don't exist yet.

These are correctly out of scope for a seam design with no hardware to validate against — flagged as open, not guessed at.
