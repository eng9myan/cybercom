from django.db import models

from platform.common.models import BaseModel


class PurchaseOrder(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("approved", "Approved"),
        ("sent", "Sent"),
        ("partial", "Partial"),
        ("received", "Received"),
        ("cancelled", "Cancelled"),
    ]

    po_number = models.CharField(max_length=50)
    vendor_id = models.UUIDField(db_index=True)
    po_date = models.DateField()
    expected_delivery = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    subtotal = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    approved_by = models.UUIDField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_procurement_purchase_orders"
        ordering = ["-created_at"]

    def __str__(self):
        return self.po_number


class POLine(BaseModel):
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    item_id = models.UUIDField(db_index=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    class Meta:
        db_table = "cycom_procurement_po_lines"
        ordering = ["created_at"]

    def __str__(self):
        return f"Line {self.id} — PO {self.po.po_number}"


class GoodsReceipt(BaseModel):
    po = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="receipts")
    receipt_date = models.DateField()
    received_by = models.UUIDField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_procurement_goods_receipts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"GR {self.id} — PO {self.po.po_number}"


class GoodsReceiptLine(BaseModel):
    goods_receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name="lines")
    po_line = models.ForeignKey(POLine, on_delete=models.PROTECT, related_name="receipt_lines")
    item_id = models.UUIDField()
    quantity_received = models.DecimalField(max_digits=10, decimal_places=3)
    batch_id = models.UUIDField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cycom_procurement_goods_receipt_lines"
        ordering = ["created_at"]

    def __str__(self):
        return f"GRL {self.id} — GR {self.goods_receipt_id}"
