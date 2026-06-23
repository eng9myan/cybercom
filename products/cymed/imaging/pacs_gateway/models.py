from django.db import models
from platform.common.models import BaseModel


class PACSNode(BaseModel):
    class Meta:
        app_label = "img_pacs"
        db_table = "cymed_img_pacs_nodes"

    code = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=255)
    ae_title = models.CharField(max_length=16)
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField(default=11112)
    protocol = models.CharField(max_length=20, choices=[
        ("dicom", "DICOM"), ("dicomweb", "DICOMweb"), ("wado", "WADO-RS"),
    ], default="dicom")
    wado_rs_url = models.CharField(max_length=500, blank=True)
    qido_rs_url = models.CharField(max_length=500, blank=True)
    stow_rs_url = models.CharField(max_length=500, blank=True)
    wado_uri_url = models.CharField(max_length=500, blank=True)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    vendor = models.CharField(max_length=100, blank=True)
    tls_enabled = models.BooleanField(default=False)
    connection_verified_at = models.DateTimeField(null=True, blank=True)
    api_key_reference = models.CharField(max_length=255, blank=True)

    class Meta:
        app_label = "img_pacs"
        db_table = "cymed_img_pacs_nodes"
        unique_together = [("tenant_id", "code")]

    def __str__(self):
        return f"{self.code} ({self.ae_title})"


class PACSQuery(BaseModel):
    class Meta:
        app_label = "img_pacs"
        db_table = "cymed_img_pacs_queries"

    pacs_node = models.ForeignKey("img_pacs.PACSNode", on_delete=models.CASCADE)
    query_type = models.CharField(max_length=20, choices=[
        ("find", "C-FIND"), ("move", "C-MOVE"), ("get", "C-GET"),
        ("qido", "QIDO-RS"), ("wado", "WADO-RS"),
    ], default="find")
    query_level = models.CharField(max_length=20, choices=[
        ("patient", "Patient"), ("study", "Study"),
        ("series", "Series"), ("image", "Image"),
    ], default="study")
    query_params = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"), ("running", "Running"),
        ("success", "Success"), ("failed", "Failed"),
    ], default="pending")
    results_count = models.PositiveIntegerField(default=0)
    executed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    response_payload = models.JSONField(default=list)
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"Query {self.query_type}/{self.query_level} — {self.status}"


class StudyRoute(BaseModel):
    class Meta:
        app_label = "img_pacs"
        db_table = "cymed_img_study_routes"

    order_item = models.ForeignKey("img_orders.ImagingOrderItem", on_delete=models.CASCADE)
    source_pacs = models.ForeignKey(
        "img_pacs.PACSNode", on_delete=models.CASCADE, related_name="outbound_routes"
    )
    destination_pacs = models.ForeignKey(
        "img_pacs.PACSNode", null=True, blank=True, on_delete=models.SET_NULL, related_name="inbound_routes"
    )
    route_type = models.CharField(max_length=20, choices=[
        ("store", "Store"), ("retrieve", "Retrieve"), ("forward", "Forward"),
    ], default="store")
    study_instance_uid = models.CharField(max_length=255, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"), ("in_progress", "In Progress"),
        ("completed", "Completed"), ("failed", "Failed"),
    ], default="pending")
    initiated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    bytes_transferred = models.PositiveBigIntegerField(default=0)
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"Route {self.route_type} — {self.status}"


class PACSEvent(BaseModel):
    class Meta:
        app_label = "img_pacs"
        db_table = "cymed_img_pacs_events"
        ordering = ["-created_at"]

    pacs_node = models.ForeignKey("img_pacs.PACSNode", on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50, choices=[
        ("study_received", "Study Received"), ("study_stored", "Study Stored"),
        ("study_deleted", "Study Deleted"), ("connection_lost", "Connection Lost"),
        ("connection_restored", "Connection Restored"), ("worklist_queried", "Worklist Queried"),
    ])
    study_instance_uid = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict)
    acknowledged = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.event_type} — {self.pacs_node.code}"
