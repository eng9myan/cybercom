from django.db import transaction
from django.utils import timezone

from products.cymed.imaging.dicom_registry.cyvault_client import CyVaultClient
from products.cymed.imaging.dicom_registry.models import DICOMInstance, StudyArchive


@transaction.atomic
def archive_dicom_instance(
    instance: DICOMInstance,
    file_bytes: bytes,
    filename: str,
    *,
    access_token: str,
    content_type: str = "application/dicom",
) -> DICOMInstance:
    """
    Uploads one DICOM instance's pixel data to CyVault and records the real
    reference on the instance (wado_url) and the parent study's archive
    record (archive_location/archive_bucket/checksum) — both fields
    existed before this as unpopulated placeholders (confirmed: no code
    anywhere wrote to them).
    """
    study = instance.series.study
    result = CyVaultClient().upload_file(
        access_token,
        file_bytes,
        filename,
        category="dicom_study",
        content_type=content_type,
        linked_model="cymed.imaging.study",
        linked_id=study.id,
    )

    instance.wado_url = result["download_url"]
    instance.save(update_fields=["wado_url", "updated_at"])

    archive, _ = StudyArchive.objects.get_or_create(
        study=study,
        defaults={"tenant_id": study.tenant_id},
    )
    archive.archive_location = result["download_url"]
    archive.archive_bucket = result.get("id", "")
    archive.checksum = result.get("checksum_sha256", "")
    archive.archived_at = timezone.now()
    archive.save(update_fields=["archive_location", "archive_bucket", "checksum", "archived_at", "updated_at"])

    return instance
