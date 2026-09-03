"""
High-level Hakeem client. Wraps VistaRPC (pull) + SFTP HL7 (push).
Falls back to FHIR proxy when HAKEEM_FHIR_URL is set (2026 roadmap).
"""
from __future__ import annotations

import io
import os
import time
from typing import Any

import requests

from .hl7_builder import build_mdm_t02, build_oru_r01
from .models import HakeemMessage
from .mumps_rpc import RpcError, VistaRpcClient


class HakeemClient:
    def __init__(self):
        self.facility_code = os.environ.get("HAKEEM_FACILITY_CODE", "")
        self.fhir_url = os.environ.get("HAKEEM_FHIR_URL", "").rstrip("/")
        self.fhir_token = os.environ.get("HAKEEM_FHIR_TOKEN", "")
        # SFTP settings loaded on demand (paramiko optional)
        self.sftp_host = os.environ.get("HAKEEM_SFTP_HOST", "")
        self.sftp_user = os.environ.get("HAKEEM_SFTP_USER", "")
        self.sftp_key = os.environ.get("HAKEEM_SFTP_KEY_PATH", "")

    # ── FHIR (preferred when available) ─────────────────────────────────
    def _fhir_get(self, path: str) -> dict | None:
        if not self.fhir_url:
            return None
        r = requests.get(f"{self.fhir_url}{path}",
                          headers={"Authorization": f"Bearer {self.fhir_token}",
                                    "Accept": "application/fhir+json"},
                          timeout=30)
        r.raise_for_status()
        return r.json()

    # ── Pull operations ─────────────────────────────────────────────────
    def get_patient(self, national_id: str) -> dict:
        start = time.time()
        # Try FHIR first
        fhir = self._fhir_get(f"/Patient?identifier={national_id}") if self.fhir_url else None
        if fhir and fhir.get("entry"):
            HakeemMessage.objects.create(
                direction="pull", transport="fhir", op="get_patient",
                subject_national_id=national_id, status="succeeded",
                response_payload=str(fhir)[:5000],
                duration_ms=int((time.time() - start) * 1000),
            )
            return fhir["entry"][0].get("resource", {})

        # Fallback: VistaRPC ORWPT ID INFO
        try:
            with VistaRpcClient() as rpc:
                raw = rpc.call("ORWPT ID INFO", national_id)
            HakeemMessage.objects.create(
                direction="pull", transport="rpc", op="ORWPT ID INFO",
                subject_national_id=national_id, status="succeeded",
                response_payload=raw[:5000],
                duration_ms=int((time.time() - start) * 1000),
            )
            return self._parse_orwpt_id_info(raw)
        except (RpcError, OSError) as exc:
            HakeemMessage.objects.create(
                direction="pull", transport="rpc", op="ORWPT ID INFO",
                subject_national_id=national_id, status="failed",
                error_message=str(exc),
                duration_ms=int((time.time() - start) * 1000),
            )
            return {}

    def get_active_meds(self, national_id: str) -> list[dict]:
        try:
            with VistaRpcClient() as rpc:
                raw = rpc.call("ORWPS ACTIVE", national_id)
            HakeemMessage.objects.create(
                direction="pull", transport="rpc", op="ORWPS ACTIVE",
                subject_national_id=national_id, status="succeeded",
                response_payload=raw[:5000],
            )
            return self._parse_orwps_active(raw)
        except (RpcError, OSError) as exc:
            HakeemMessage.objects.create(
                direction="pull", transport="rpc", op="ORWPS ACTIVE",
                subject_national_id=national_id, status="failed",
                error_message=str(exc),
            )
            return []

    def get_lab_results(self, national_id: str) -> list[dict]:
        try:
            with VistaRpcClient() as rpc:
                raw = rpc.call("ORWLRR INTERIM", national_id)
            HakeemMessage.objects.create(
                direction="pull", transport="rpc", op="ORWLRR INTERIM",
                subject_national_id=national_id, status="succeeded",
                response_payload=raw[:5000],
            )
            return self._parse_orwlrr(raw)
        except (RpcError, OSError) as exc:
            HakeemMessage.objects.create(
                direction="pull", transport="rpc", op="ORWLRR INTERIM",
                subject_national_id=national_id, status="failed",
                error_message=str(exc),
            )
            return []

    # ── Push operations ─────────────────────────────────────────────────
    def push_lab_results(self, *, patient_national_id: str, patient_name: str,
                          observations: list[dict]) -> str:
        msg = build_oru_r01(patient_national_id=patient_national_id,
                             patient_name=patient_name,
                             observations=observations)
        filename = f"CYMED_ORU_{patient_national_id}_{int(time.time())}.hl7"
        try:
            self._sftp_upload(filename, msg.encode())
            HakeemMessage.objects.create(
                direction="push", transport="sftp_hl7", op="ORU^R01",
                subject_national_id=patient_national_id, status="succeeded",
                request_payload=msg[:5000],
            )
        except Exception as exc:  # noqa: BLE001
            HakeemMessage.objects.create(
                direction="push", transport="sftp_hl7", op="ORU^R01",
                subject_national_id=patient_national_id, status="failed",
                request_payload=msg[:5000], error_message=str(exc),
            )
            raise
        return filename

    def push_discharge_summary(self, *, patient_national_id: str,
                                patient_name: str, summary_text: str) -> str:
        msg = build_mdm_t02(patient_national_id=patient_national_id,
                             patient_name=patient_name,
                             document_type="Discharge Summary",
                             document_text=summary_text)
        filename = f"CYMED_MDM_{patient_national_id}_{int(time.time())}.hl7"
        try:
            self._sftp_upload(filename, msg.encode())
            HakeemMessage.objects.create(
                direction="push", transport="sftp_hl7", op="MDM^T02",
                subject_national_id=patient_national_id, status="succeeded",
                request_payload=msg[:5000],
            )
        except Exception as exc:  # noqa: BLE001
            HakeemMessage.objects.create(
                direction="push", transport="sftp_hl7", op="MDM^T02",
                subject_national_id=patient_national_id, status="failed",
                request_payload=msg[:5000], error_message=str(exc),
            )
            raise
        return filename

    def _sftp_upload(self, filename: str, data: bytes):
        try:
            import paramiko
        except ImportError as e:
            raise RuntimeError("paramiko not installed") from e
        pkey = paramiko.RSAKey.from_private_key_file(self.sftp_key)
        with paramiko.Transport((self.sftp_host, 22)) as t:
            t.connect(username=self.sftp_user, pkey=pkey)
            with paramiko.SFTPClient.from_transport(t) as sftp:
                with sftp.open(f"/incoming/cymed/{filename}", "wb") as fh:
                    fh.write(data)

    # ── VistaRPC response parsers ───────────────────────────────────────
    @staticmethod
    def _parse_orwpt_id_info(raw: str) -> dict:
        # RPC returns caret-delimited: NAME^DOB^SEX^SSN^...
        parts = raw.split("^")
        return {
            "name": parts[0] if len(parts) > 0 else "",
            "dob": parts[1] if len(parts) > 1 else "",
            "sex": parts[2] if len(parts) > 2 else "",
            "national_id": parts[3] if len(parts) > 3 else "",
        }

    @staticmethod
    def _parse_orwps_active(raw: str) -> list[dict]:
        rows = raw.strip().split("\n")
        out = []
        for row in rows:
            parts = row.split("^")
            if len(parts) >= 4:
                out.append({
                    "med_id": parts[0],
                    "name": parts[1],
                    "dose": parts[2],
                    "sig": parts[3],
                })
        return out

    @staticmethod
    def _parse_orwlrr(raw: str) -> list[dict]:
        rows = raw.strip().split("\n")
        out = []
        for row in rows:
            parts = row.split("^")
            if len(parts) >= 5:
                out.append({
                    "loinc": parts[0], "name": parts[1],
                    "value": parts[2], "units": parts[3],
                    "ref_range": parts[4],
                })
        return out
