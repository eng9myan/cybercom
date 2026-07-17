from django.db import models

from platform.common.models import BaseModel
from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Partner
from products.cycom.inventory.models import Product, Warehouse


class PurchaseRequest(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending_approval", "Pending Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("converted", "Converted to PO"),
    ]

    requested_by = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=150, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_procurement_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"PR-{str(self.id)[:8]} ({self.status})"


class PurchaseRequestLine(BaseModel):
    request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="purchase_request_lines")
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    estimated_unit_cost = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    class Meta:
        db_table = "cycom_procurement_request_lines"
        ordering = ["id"]


class PurchaseOrder(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("approved", "Approved"),
        ("received", "Received"),
        ("partially_received", "Partially Received"),
    ]

    vendor = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name="purchase_orders")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="purchase_orders")
    source_request = models.ForeignKey(
        PurchaseRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="purchase_orders"
    )
    currency = models.CharField(max_length=10, default="JOD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    class Meta:
        db_table = "cycom_procurement_orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"PO-{str(self.id)[:8]} ({self.status})"


class PurchaseOrderLine(BaseModel):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="purchase_order_lines")
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=4)
    quantity_received = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    # GL offset for the resulting inventory receipt (e.g. GRNI clearing).
    offset_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="purchase_order_lines"
    )

    class Meta:
        db_table = "cycom_procurement_order_lines"
        ordering = ["id"]

    @property
    def quantity_remaining(self):
        return self.quantity - self.quantity_received
