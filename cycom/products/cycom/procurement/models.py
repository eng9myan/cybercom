from decimal import Decimal

from django.db import models

from platform.common.models import BaseModel
from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Partner
from products.cycom.company.models import Company
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

    @property
    def total_amount(self):
        return sum(
            (l.quantity * l.estimated_unit_cost for l in self.lines.all()), Decimal("0")
        )


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
    company = models.ForeignKey(
        Company, on_delete=models.PROTECT, null=True, blank=True, related_name="purchase_orders"
    )

    class Meta:
        db_table = "cycom_procurement_orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"PO-{str(self.id)[:8]} ({self.status})"

    @property
    def total_amount(self):
        return sum((l.quantity * l.unit_cost for l in self.lines.all()), Decimal("0"))


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


class RequestForQuotation(BaseModel):
    """Sent to several vendors for the same purchase request; each vendor's
    reply becomes a VendorBid. Awarding one bid creates the real
    PurchaseOrder and marks the rest lost — RFQs never become POs any
    other way."""

    STATUS_CHOICES = [
        ("open", "Open"),
        ("awarded", "Awarded"),
        ("cancelled", "Cancelled"),
    ]

    source_request = models.ForeignKey(
        PurchaseRequest, on_delete=models.CASCADE, related_name="rfqs"
    )
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")

    class Meta:
        db_table = "cycom_procurement_rfqs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"RFQ-{str(self.id)[:8]} ({self.status})"


class VendorBid(BaseModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("submitted", "Submitted"),
        ("won", "Won"),
        ("lost", "Lost"),
    ]

    rfq = models.ForeignKey(RequestForQuotation, on_delete=models.CASCADE, related_name="bids")
    vendor = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name="vendor_bids")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_procurement_vendor_bids"
        ordering = ["-created_at"]
        unique_together = [("rfq", "vendor")]

    def __str__(self):
        return f"{self.vendor} bid on {self.rfq}"

    @property
    def total_amount(self):
        return sum((l.quantity * l.unit_cost for l in self.lines.all()), Decimal("0"))


class VendorBidLine(BaseModel):
    bid = models.ForeignKey(VendorBid, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="vendor_bid_lines")
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    lead_time_days = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cycom_procurement_vendor_bid_lines"
        ordering = ["id"]
