import uuid
from django.db import models
from django.utils import timezone
from platform.common.models import PlatformModel

class IntegrationPartner(PlatformModel):
    """
    Registry of external partners (hospitals, retail stores, government gateways).
    """
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    protocol = models.CharField(max_length=50, default="fhir")  # fhir, hl7, rest, soap, sftp
    direction = models.CharField(max_length=20, default="bidirectional")  # inbound, outbound, bidirectional
    active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "platform_integration_partners"

    def __str__(self) -> str:
        return f"Partner({self.name}, {self.protocol})"


class ConnectorConfig(PlatformModel):
    """
    Configurations for individual protocol endpoints (e.g. keycloak, SFTP paths, SOAP urls).
    """
    partner = models.ForeignKey(IntegrationPartner, on_delete=models.CASCADE, related_name="connectors")
    name = models.CharField(max_length=255)
    connector_type = models.CharField(max_length=50)  # fhir, hl7v2, dicom, ldap, keycloak, soap, rest
    endpoint_url = models.CharField(max_length=1000)
    auth_config = models.JSONField(default=dict, blank=True)  # client-id, client-secret vaults
    active = models.BooleanField(default=True)
    sync_interval_seconds = models.PositiveIntegerField(default=300)

    class Meta:
        db_table = "platform_connector_configs"

    def __str__(self) -> str:
        return f"Connector({self.name}, {self.connector_type})"


class TransformationMapping(PlatformModel):
    """
    Transformation expressions and mappings (e.g., HL7 to FHIR or custom JSON paths).
    """
    name = models.CharField(max_length=255)
    source_format = models.CharField(max_length=50)  # hl7v2, fhir, xml, json
    target_format = models.CharField(max_length=50)  # json, fhir, hl7v2
    mapping_rules = models.JSONField()  # maps source keys to target keys
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "platform_transformation_mappings"

    def __str__(self) -> str:
        return f"Mapping({self.name}: {self.source_format} -> {self.target_format})"


class MessageAuditLog(models.Model):
    """
    Immutable tracking ledger for every message processed through the Integration Hub.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    partner = models.ForeignKey(IntegrationPartner, on_delete=models.SET_NULL, null=True, blank=True)
    connector_type = models.CharField(max_length=50, db_index=True)
    direction = models.CharField(max_length=20, db_index=True)  # inbound, outbound
    payload_size_bytes = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, db_index=True)  # success, failed
    error_message = models.TextField(blank=True)
    duration_ms = models.PositiveIntegerField(default=0)
    processed_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "platform_integration_message_audits"
        ordering = ["-processed_at"]
