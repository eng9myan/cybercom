from django.db import models
from platform.common.models import BaseModel


class DICOMStudy(BaseModel):
    class Meta:
        app_label = "img_dicom"
        db_table = "cymed_img_dicom_studies"

    order_item = models.OneToOneField(
        "img_orders.ImagingOrderItem", null=True, blank=True, on_delete=models.SET_NULL, related_name="dicom_study"
    )
    pacs_node = models.ForeignKey("img_pacs.PACSNode", null=True, blank=True, on_delete=models.SET_NULL)
    study_instance_uid = models.CharField(max_length=255, unique=True, db_index=True)
    accession_number = models.CharField(max_length=100, blank=True, db_index=True)
    patient_id = models.UUIDField(db_index=True)
    modality = models.CharField(max_length=20)
    study_date = models.DateField(null=True, blank=True)
    study_time = models.TimeField(null=True, blank=True)
    study_description = models.CharField(max_length=255, blank=True)
    referring_physician = models.CharField(max_length=255, blank=True)
    series_count = models.PositiveIntegerField(default=0)
    instance_count = models.PositiveIntegerField(default=0)
    storage_size_mb = models.PositiveIntegerField(default=0)
    archive_status = models.CharField(max_length=20, choices=[
        ("online", "Online"), ("nearline", "Nearline"), ("offline", "Offline"),
    ], default="online")
    received_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.study_instance_uid} ({self.modality})"


class DICOMSeries(BaseModel):
    class Meta:
        app_label = "img_dicom"
        db_table = "cymed_img_dicom_series"

    study = models.ForeignKey("img_dicom.DICOMStudy", on_delete=models.CASCADE, related_name="series")
    series_instance_uid = models.CharField(max_length=255, unique=True, db_index=True)
    series_number = models.PositiveIntegerField(null=True, blank=True)
    series_description = models.CharField(max_length=255, blank=True)
    modality = models.CharField(max_length=20, blank=True)
    body_part = models.CharField(max_length=100, blank=True)
    laterality = models.CharField(max_length=20, blank=True)
    instance_count = models.PositiveIntegerField(default=0)
    slice_thickness = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    pixel_spacing = models.CharField(max_length=50, blank=True)
    acquisition_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"Series {self.series_instance_uid}"


class DICOMInstance(BaseModel):
    class Meta:
        app_label = "img_dicom"
        db_table = "cymed_img_dicom_instances"

    series = models.ForeignKey("img_dicom.DICOMSeries", on_delete=models.CASCADE, related_name="instances")
    sop_instance_uid = models.CharField(max_length=255, unique=True, db_index=True)
    sop_class_uid = models.CharField(max_length=255, blank=True)
    instance_number = models.PositiveIntegerField(null=True, blank=True)
    image_type = models.CharField(max_length=100, blank=True)
    rows = models.PositiveIntegerField(null=True, blank=True)
    columns = models.PositiveIntegerField(null=True, blank=True)
    bits_allocated = models.PositiveSmallIntegerField(null=True, blank=True)
    window_center = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    window_width = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    wado_url = models.TextField(blank=True)
    transfer_syntax_uid = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Instance {self.sop_instance_uid}"


class StudyArchive(BaseModel):
    class Meta:
        app_label = "img_dicom"
        db_table = "cymed_img_study_archives"

    study = models.OneToOneField("img_dicom.DICOMStudy", on_delete=models.CASCADE, related_name="archive")
    archive_tier = models.CharField(max_length=20, choices=[
        ("hot", "Hot"), ("warm", "Warm"), ("cold", "Cold"),
    ], default="hot")
    retention_years = models.PositiveSmallIntegerField(default=10)
    compressed = models.BooleanField(default=False)
    compression_type = models.CharField(max_length=50, blank=True)
    compression_ratio = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    archive_location = models.TextField(blank=True)
    archive_bucket = models.CharField(max_length=255, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    retrieval_sla_hours = models.PositiveIntegerField(default=1)
    checksum = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return f"Archive {self.study.study_instance_uid} — {self.archive_tier}"
