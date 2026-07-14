from django.db import models

from platform.common.models import BaseModel


class ImagingResult(BaseModel):
    class Meta:
        app_label = "img_results"
        db_table = "cymed_img_results"

    order_item = models.OneToOneField(
        "img_orders.ImagingOrderItem", on_delete=models.CASCADE, related_name="result"
    )
    report = models.OneToOneField(
        "img_reporting.RadiologyReport",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="result",
    )
    status = models.CharField(
        max_length=30,
        choices=[
            ("pending", "Pending"),
            ("preliminary", "Preliminary"),
            ("final", "Final"),
            ("amended", "Amended"),
        ],
        default="pending",
        db_index=True,
    )
    result_date = models.DateTimeField(null=True, blank=True)
    communicated_to = models.UUIDField(null=True, blank=True)
    communicated_at = models.DateTimeField(null=True, blank=True)
    communication_method = models.CharField(max_length=50, blank=True)
    fhir_diagnostic_report_id = models.CharField(max_length=255, blank=True)
    tat_minutes = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Result {self.id} — {self.status}"


class StructuredMeasurement(BaseModel):
    class Meta:
        app_label = "img_results"
        db_table = "cymed_img_measurements"

    result = models.ForeignKey(
        "img_results.ImagingResult", on_delete=models.CASCADE, related_name="measurements"
    )
    measurement_name = models.CharField(max_length=255)
    value = models.DecimalField(max_digits=12, decimal_places=4)
    unit = models.CharField(max_length=50)
    body_site = models.CharField(max_length=100, blank=True)
    laterality = models.CharField(max_length=20, blank=True)
    reference_range_low = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    reference_range_high = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    loinc_code = models.CharField(max_length=20, blank=True)
    dicom_sr_reference = models.CharField(max_length=255, blank=True)
    method = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.measurement_name}: {self.value} {self.unit}"


class ResultCommunication(BaseModel):
    class Meta:
        app_label = "img_results"
        db_table = "cymed_img_result_communications"

    result = models.ForeignKey(
        "img_results.ImagingResult", on_delete=models.CASCADE, related_name="communications"
    )
    communicated_to = models.UUIDField()
    communicated_by = models.UUIDField()
    communication_method = models.CharField(
        max_length=50,
        choices=[
            ("portal", "Patient Portal"),
            ("phone", "Phone"),
            ("fax", "Fax"),
            ("email", "Email"),
            ("ehr", "EHR Integration"),
        ],
        default="portal",
    )
    communicated_at = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
