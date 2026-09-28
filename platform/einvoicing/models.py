from django.db import models

from platform.common.models import BaseModel

from .hashing import GENESIS_PIH


class EInvoiceSequence(BaseModel):
    """Per-(tenant, scope) gap-free counter + hash chain head.

    `scope` is a free string identifying the issuing unit — an organization id,
    or "<org>:<device>" where a regulator requires per-device sequences (ZATCA).
    `clear_invoice` locks this row (`select_for_update`) for the duration of a
    clearance so ICVs are dense and the PIH chain is linear even under
    concurrent invoicing.
    """

    scope = models.CharField(max_length=200, db_index=True)
    mode = models.CharField(max_length=16)          # jo_jofotara | sa_zatca | eu_peppol | national modes
    next_icv = models.PositiveBigIntegerField(default=1)
    last_hash = models.TextField(default=GENESIS_PIH)

    class Meta:
        db_table = "platform_einvoice_sequences"
        unique_together = [("tenant_id", "scope", "mode")]


class EInvoiceInteraction(BaseModel):
    """Audit trail of every clearance attempt (immutable operational log)."""

    mode = models.CharField(max_length=16)
    invoice_ref = models.CharField(max_length=200, db_index=True)   # the source Invoice.number
    invoice_uuid = models.UUIDField()
    icv = models.PositiveBigIntegerField()
    pih = models.TextField()
    invoice_hash = models.TextField()
    status = models.CharField(max_length=16, default="pending")     # pending|cleared|reported|rejected
    provider_reference = models.CharField(max_length=200, blank=True)
    qr = models.TextField(blank=True)
    request_xml_sha = models.CharField(max_length=64, blank=True)
    response = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    # The legal document itself (national formats). Several mandates
    # (IT, MX, BR) require the issuer to retain the exact file; it's also
    # what the user downloads to file manually before a transport exists.
    document = models.TextField(blank=True)
    document_filename = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "platform_einvoice_interactions"
        ordering = ["-created_at"]


class EInvoiceProfile(BaseModel):
    """The issuing taxpayer's e-invoicing identity, one per tenant.

    Core address/identity fields are shared by every format; `national`
    holds the per-format keys each format's FieldSpecs declare (IT
    regime_fiscale, MX regimen_fiscal, IN state_code, ...). Blank core
    fields fall back to TenantProfile (legal_name, vat_number) in the bridge.
    """

    legal_name = models.CharField(max_length=300, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    street = models.CharField(max_length=200, blank=True)
    building_number = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    region = models.CharField(max_length=60, blank=True)
    email = models.EmailField(blank=True)
    national = models.JSONField(default=dict, blank=True)

    CORE_FIELDS = ("legal_name", "tax_id", "street", "building_number", "city",
                   "postal_code", "region", "email")

    class Meta:
        db_table = "platform_einvoice_profiles"
        constraints = [models.UniqueConstraint(fields=["tenant_id"], name="uniq_einvoice_profile_tenant")]
