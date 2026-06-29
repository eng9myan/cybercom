import uuid

from django.db import models
from django.utils import timezone

from platform.common.models import PlatformModel


class DataAsset(PlatformModel):
    """
    Catalog of all logical tables, views, and object stores across the platform (Data Catalog).
    """

    ASSET_TYPE_CHOICES = [
        ("table", "Database Table"),
        ("lakehouse", "Iceberg Lakehouse Table"),
        ("bucket", "GCS Bucket"),
        ("view", "Database View"),
    ]
    name = models.CharField(max_length=255, unique=True)
    asset_type = models.CharField(max_length=50, choices=ASSET_TYPE_CHOICES, default="lakehouse")
    physical_path = models.CharField(max_length=1000)
    schema_definition = models.JSONField(default=dict)
    pii_columns = models.JSONField(default=list, blank=True)  # Columns marked as PII
    phi_columns = models.JSONField(
        default=list, blank=True
    )  # Columns marked as PHI (HIPAA protection)
    data_residency_region = models.CharField(max_length=100, default="me-central-1")

    class Meta:
        db_table = "platform_data_assets"

    def __str__(self) -> str:
        return f"DataAsset({self.name}, {self.asset_type})"


class DataLineage(models.Model):
    """
    Directed lineage graph tracing how data flows between source assets and target metrics.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    source_asset = models.ForeignKey(
        DataAsset, on_delete=models.CASCADE, related_name="downstream_lineage"
    )
    target_asset = models.ForeignKey(
        DataAsset, on_delete=models.CASCADE, related_name="upstream_lineage"
    )
    transformation_job = models.CharField(max_length=255)  # dbt model name or Airflow DAG ID
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "platform_data_lineage"
        unique_together = [("source_asset", "target_asset", "transformation_job")]


class DataQualityRule(PlatformModel):
    """
    Assertions run by the Data Quality Engine to validate data assets.
    """

    asset = models.ForeignKey(DataAsset, on_delete=models.CASCADE, related_name="quality_rules")
    column_name = models.CharField(max_length=255)
    assertion_type = models.CharField(max_length=50)  # not_null, min_value, format_email, unique
    assertion_params = models.JSONField(default=dict, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "platform_data_quality_rules"

    def __str__(self) -> str:
        return f"QualityRule({self.asset.name}.{self.column_name} is {self.assertion_type})"


class MasterDataMap(PlatformModel):
    """
    Entity mappings and record linkage for golden record merging (Patient, Citizen, Customer).
    """

    entity_type = models.CharField(max_length=100, db_index=True)  # Patient, Employee, Citizen
    source_system = models.CharField(max_length=100)  # Epic, Cerner, Odoo, SAP
    source_id = models.CharField(max_length=255)
    golden_record_id = models.UUIDField(db_index=True)
    match_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)

    class Meta:
        db_table = "platform_master_data_maps"
        unique_together = [("entity_type", "source_system", "source_id")]


class CDCPipelineLog(models.Model):
    """
    Audit logging for CDC pipelines monitoring database WAL changes.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    table_name = models.CharField(max_length=255)
    records_synced = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=50, default="synced")
    last_processed_lsn = models.CharField(max_length=100, blank=True)
    synced_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "platform_cdc_pipeline_logs"
        ordering = ["-synced_at"]
