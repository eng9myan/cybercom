import hashlib

from django.db import models

from platform.common.models import BaseModel


class FileCategory(models.TextChoices):
    GENERIC = "generic", "Generic"
    # Cymed imaging's PACS/DICOM registry has zero file storage today
    # (confirmed: no file/DICOM fields anywhere in cymed/products/cymed/imaging)
    # — this category is the first real consumer, referenced by
    # linked_model="cymed.imaging.study" + linked_id from cymed's own DB
    # (cross-service reference, not a Django FK — cymed and CyVault are
    # separate Django projects/databases, same pattern as cymed calling
    # cyshop's registration API service-to-service).
    DICOM_STUDY = "dicom_study", "DICOM Study"
    CATALOG_IMAGE = "catalog_image", "Catalog Image"
    INVOICE_PDF = "invoice_pdf", "Invoice PDF"
    PATIENT_DOCUMENT = "patient_document", "Patient Health Document"


class FileObject(BaseModel):
    """
    CyVault's core primitive: one uploaded file, stored through whichever
    backend core/settings.py's STORAGES.default points at (local disk in
    dev/test, S3-compatible — AWS S3 or self-hosted MinIO — in production).
    `file.url` is backend-transparent: FileSystemStorage returns a plain
    MEDIA_URL path, S3Boto3Storage returns a real presigned URL when
    AWS_QUERYSTRING_AUTH is enabled (the configured default) — callers
    never need to know which backend is active.
    """

    file = models.FileField(upload_to="cyvault/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=150, blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)
    checksum_sha256 = models.CharField(max_length=64, blank=True, db_index=True)
    category = models.CharField(max_length=30, choices=FileCategory.choices, default=FileCategory.GENERIC)
    # Generic cross-service linkage — e.g. "cymed.imaging.study" +
    # a UUID from cymed's own database. Never a Django FK: CyVault, cymed,
    # and cyshop are separate Django projects/databases (same reasoning as
    # DemoProvisioningService calling cyshop's API instead of an ORM join).
    linked_model = models.CharField(max_length=100, blank=True)
    linked_id = models.UUIDField(null=True, blank=True)
    uploaded_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyvault_files"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["linked_model", "linked_id"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return self.original_filename

    def compute_checksum(self) -> str:
        """Real SHA-256 over the stored file content — DICOM archiving in
        particular needs integrity verification, not just a filename."""
        hasher = hashlib.sha256()
        self.file.seek(0)
        for chunk in self.file.chunks():
            hasher.update(chunk)
        self.file.seek(0)
        return hasher.hexdigest()
