"""
CyMed Pharmacy — Inventory Bridge (CyCom ERP Integration)
CyCom ERP owns inventory. This bridge publishes consumption events
and queries inventory status via CyIntegrationHub.
NO ERP inventory logic inside pharmacy.
"""
from django.db import models
from platform.common.models import BaseModel


class MedicationConsumptionEvent(BaseModel):
    """
    Records medication consumption at point of dispensing.
    Published as 'cymed.inventory.consumed' event for CyCom ERP to process.
    CyCom ERP handles the actual inventory deduction.
    """
    dispense_order_id = models.UUIDField(db_index=True)
    prescription_id = models.UUIDField(null=True, blank=True)
    patient_id = models.UUIDField(db_index=True)
    drug_code = models.CharField(max_length=100, db_index=True)
    drug_name = models.CharField(max_length=500)
    ndc_code = models.CharField(max_length=50, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    quantity_unit = models.CharField(max_length=50)
    lot_number = models.CharField(max_length=100, blank=True)
    dispensed_from_location = models.CharField(max_length=255, blank=True)
    dispensed_at = models.DateTimeField()

    # ERP sync status
    erp_sync_status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("synced", "Synced"), ("failed", "Failed"), ("manual", "Manual")],
        default="pending"
    )
    erp_transaction_id = models.CharField(max_length=255, blank=True)
    erp_synced_at = models.DateTimeField(null=True, blank=True)
    erp_error = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_inventory_consumption_events"
        indexes = [
            models.Index(fields=["tenant_id", "erp_sync_status"]),
            models.Index(fields=["drug_code", "dispensed_at"]),
        ]


class InventoryQueryResult(BaseModel):
    """
    Cache of inventory status queries to CyCom ERP via CyIntegrationHub.
    Prevents repeated round-trips to ERP for the same drug.
    """
    drug_code = models.CharField(max_length=100, db_index=True)
    drug_name = models.CharField(max_length=500, blank=True)
    location = models.CharField(max_length=255, blank=True)
    quantity_on_hand = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    quantity_unit = models.CharField(max_length=50, blank=True)
    reorder_level = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    is_below_reorder = models.BooleanField(default=False)
    is_out_of_stock = models.BooleanField(default=False)
    expiry_date = models.DateField(null=True, blank=True)
    erp_item_id = models.CharField(max_length=255, blank=True)      # CyCom ERP item ID
    cached_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymed_inventory_query_cache"
        indexes = [
            models.Index(fields=["tenant_id", "drug_code"]),
        ]
