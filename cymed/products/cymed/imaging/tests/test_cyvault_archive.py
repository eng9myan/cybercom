"""
Tests: Cymed Imaging -> CyVault DICOM archiving integration.
CyVault previously had DICOMInstance.wado_url and StudyArchive.archive_location/
archive_bucket/checksum as real fields with nothing ever populating them —
this exercises the real call chain that now does, mocking only the HTTP
boundary (cymed and CyVault are separate services), same pattern as
cymart's cydrive_client tests.
"""

import uuid
from unittest.mock import Mock, patch

import pytest

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()


def make_instance(tenant_id):
    from products.cymed.imaging.dicom_registry.models import DICOMInstance, DICOMSeries, DICOMStudy

    study = DICOMStudy.objects.create(
        tenant_id=tenant_id,
        patient_id=PATIENT,
        study_instance_uid=f"1.2.840.{uuid.uuid4().hex}",
        modality="ct",
    )
    series = DICOMSeries.objects.create(
        tenant_id=tenant_id,
        study=study,
        series_instance_uid=f"1.2.840.{uuid.uuid4().hex}.1",
    )
    return DICOMInstance.objects.create(
        tenant_id=tenant_id,
        series=series,
        sop_instance_uid=f"1.2.840.{uuid.uuid4().hex}.1.1",
    )


@pytest.mark.django_db
class TestCyVaultArchiveIntegration:
    @patch("products.cymed.imaging.dicom_registry.cyvault_client.httpx.post")
    def test_archive_instance_populates_wado_url_and_study_archive(self, mock_post):
        from products.cymed.imaging.dicom_registry.models import StudyArchive
        from products.cymed.imaging.dicom_registry.services import archive_dicom_instance

        file_id = str(uuid.uuid4())
        mock_post.return_value = Mock(
            status_code=201,
            json=lambda: {
                "id": file_id,
                "download_url": "https://cyvault.internal/media/cyvault/2026/07/study.dcm",
                "checksum_sha256": "abc123",
            },
        )

        instance = make_instance(TENANT)
        archive_dicom_instance(instance, b"fake dicom bytes", "study.dcm", access_token="tok")

        instance.refresh_from_db()
        assert instance.wado_url == "https://cyvault.internal/media/cyvault/2026/07/study.dcm"

        archive = StudyArchive.objects.get(study=instance.series.study)
        assert archive.archive_bucket == file_id
        assert archive.checksum == "abc123"
        assert archive.archived_at is not None

        sent_args, sent_kwargs = mock_post.call_args
        assert sent_args[0].endswith("/files/files/")
        assert sent_kwargs["headers"]["Authorization"] == "Bearer tok"
        assert sent_kwargs["data"]["linked_model"] == "cymed.imaging.study"
        assert sent_kwargs["data"]["linked_id"] == str(instance.series.study.id)

    @patch("products.cymed.imaging.dicom_registry.cyvault_client.httpx.post")
    def test_cyvault_rejection_raises_and_does_not_touch_instance(self, mock_post):
        from products.cymed.imaging.dicom_registry.cyvault_client import CyVaultIntegrationError
        from products.cymed.imaging.dicom_registry.services import archive_dicom_instance

        mock_post.return_value = Mock(status_code=400, text="bad request")
        instance = make_instance(TENANT)

        with pytest.raises(CyVaultIntegrationError):
            archive_dicom_instance(instance, b"x", "study.dcm", access_token="tok")

        instance.refresh_from_db()
        assert instance.wado_url == ""
