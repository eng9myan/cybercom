"""
Cymed -> CyVault integration: DICOM instance/study archiving. Cymed and
CyVault are separate Django projects/databases (separate deployables) —
this is a real network boundary, not a Python import, same as cymart's
cydrive_client.py or platform/tenant/services.py's cyshop adapter call.

CyVault's dicom_registry integration was previously a genuinely unimplemented
seam: DICOMInstance.wado_url and StudyArchive.archive_location/archive_bucket/
checksum existed as plain text fields with nothing ever populating them.
"""

import logging

import httpx
from django.conf import settings

logger = logging.getLogger("cymed.cyvault_integration")


class CyVaultIntegrationError(Exception):
    pass


def _base_url() -> str:
    return getattr(settings, "CYVAULT_BASE_URL", None) or "http://localhost:8030/api/v1"


def _timeout_seconds() -> float:
    return float(getattr(settings, "CYVAULT_REQUEST_TIMEOUT_SECONDS", 15))


class CyVaultClient:
    def upload_file(
        self,
        access_token: str,
        file_bytes: bytes,
        filename: str,
        *,
        category: str,
        content_type: str = "application/octet-stream",
        linked_model: str = "",
        linked_id: "str | None" = None,
    ) -> dict:
        """Uploads one file to CyVault, returns the created FileObject
        payload (id, download_url, checksum_sha256, ...). Raises
        CyVaultIntegrationError on any non-2xx response or network failure —
        callers decide whether that should block the DICOM ingest or retry,
        this doesn't swallow the error."""
        url = f"{_base_url()}/files/files/"
        data = {"category": category}
        if linked_model:
            data["linked_model"] = linked_model
        if linked_id:
            data["linked_id"] = str(linked_id)

        try:
            response = httpx.post(
                url,
                data=data,
                files={"file": (filename, file_bytes, content_type)},
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=_timeout_seconds(),
            )
        except httpx.HTTPError as exc:
            logger.error("CyVault upload failed for %s: %s", filename, exc)
            raise CyVaultIntegrationError(f"Could not reach CyVault: {exc}") from exc

        if response.status_code >= 400:
            logger.error(
                "CyVault rejected upload for %s: %s %s", filename, response.status_code, response.text
            )
            raise CyVaultIntegrationError(
                f"CyVault rejected upload ({response.status_code}): {response.text}"
            )

        return response.json()
